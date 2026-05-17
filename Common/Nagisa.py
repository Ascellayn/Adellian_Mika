from .Globals import *;
from . import Mika;



def Update() -> None:
	if (not File.Exists("repositories.json")):
		File.JSON_Write("repositories.json", ["https://repo.sirio-network.com/adellian", "http://127.0.0.1:7040/"]);

	Nagisa_Packages: Type.Nagisa_Packages = {
		"Last_Update": 0,
		"Error": [],
		"Packages": []
	};

	REPOSITORIES: list[str] = cast(list[str], File.JSON_Read("repositories.json"));
	total: int = 0;
	u_init: float = Time.Get_Unix(True);
	for i, repo in enumerate(REPOSITORIES, start=1):
		Log.Stateless(f"GET [{i}/{len(REPOSITORIES)}]: {repo}...");
		try:
			R: httpx.Response = httpx.get(repo, headers=HEADERS);
			if (R.status_code != 200): Nagisa_Packages["Error"].append(f"{R.status_code}: {repo}"); continue;
			npkg: Type.Nagisa_Packages = cast(Type.Nagisa_Packages, R.json());

			for e in npkg["Error"]: Nagisa_Packages["Error"].append(f"Nagisa [{i}]: {e}");
			for p in npkg["Packages"]: Nagisa_Packages["Packages"].append(p);
			
			total += len(R.content);
			Log.Awaited().OK(f"{len(npkg['Error'])} NEs - {round(len(R.content) / 1024, 2)}KiB");
		except Exception as E: Log.Awaited().EXCEPTION(E, Traceback=False);

	u_diff: float = Time.Get_Unix(True) - u_init;
	Log.Stateless(f"Fetched {round(total / 1024, 2)}KiB in {Time.Elapsed_String(u_diff, Show_Until=-1)} ({round((total / u_diff) / 1024, 2)}KiB/s)");
	for e in Nagisa_Packages["Error"]: Log.Error(e);

	oldPackages: list[Type.MikaRoll_Header] = cast(Type.Nagisa_Packages, File.JSON_Read("Nagisa.cache", True))["Packages"] if (File.Exists("Nagisa.cache")) else [];
	Updated: int = 0; New: int = 0;
	opkgs: dict[str, tuple[int, ...] | None] = {};
	for opkg in oldPackages:
		opkgs[opkg["ID"]] = opkg["Version"];

	for pkg in Nagisa_Packages["Packages"]:
		if (pkg["ID"] not in opkgs.keys()): New += 1; continue;
		if (pkg["Version"] != opkgs[pkg["ID"]]): Updated +=1;

	if (Updated != 0): Log.Info(f"{Updated} packages have been updated.");
	if (New != 0): Log.Info(f"{New} new packages have been cached.");
	if (Updated == 0 and New == 0): Log.Info(f"No new packages have been added or updated.");
	File.JSON_Write("Nagisa.cache", Nagisa_Packages, True);





def Download(Requested: list[str]) -> Type.Nagisa_Downloads:
	if (not File.Exists("Nagisa.cache")): Log.Critical(f"`Nagisa.cache` is missing, run `apm update` first!"); exit(1);
	# Gather all installable packages
	Cached: Type.Nagisa_Packages = cast(Type.Nagisa_Packages, File.JSON_Read("Nagisa.cache", True));
	PKGs: dict[str, list[str]] = {};
	idx: dict[str, int] = {};
	for i, mpkg in enumerate(Cached["Packages"]):
		PKGs[mpkg["ID"]] = [];
		idx[mpkg['ID']] = i;
		for opt in mpkg["Options"]:
			PKGs[mpkg["ID"]].append(opt["Name"]);



	# Requested Packages
	Packages: list[list[str]] = [];
	for pkg in Requested:
		if ("¤" in pkg): Packages.append(pkg.split("¤", 1)); continue;
		Packages.append([pkg]);

	# Validate against cache
	for i, pkg in enumerate(Packages):
		if (pkg[0] not in PKGs.keys()): Log.Critical(f"Package \"{pkg[0]}\" does not exist."); exit(1);
		if (len(pkg) == 1):
			if (len(Cached["Packages"][idx[pkg[0]]]["Options"]) != 1):
				TUI.Init();
				TUI.Prompt(f"Missing Option", f"You have selected the package \"{pkg[0]}\" for install, but did not specify which version to install!\n You will need to select it manually.")
				entries: TUI.Entries = [
					TUI.Entry(20, f"Package Option Selection", Bold=True),
					TUI.Entry(20, "")
				];
				for opt in Cached["Packages"][idx[pkg[0]]]["Options"]:
					entries.append(TUI.Entry(2, opt["Name"], opt["Description"], Value=opt["Name"]));

				Option: str | None = TUI.Menu(entries); TUI.Exit();
				if (not Option): Log.Error(f"Installation aborted."); exit(0);

				Packages[i].append(Option);
			else:
				Packages[i].append(Cached["Packages"][idx[pkg[0]]]["Options"][0]["Name"]);
				Log.Warning(f"No option specified for {pkg[0]}, automatically selected \"{Packages[i][1]}\" as it was the only one available.");



	Log.Stateless(f"Downloading {len(Packages)} packages...");
	# TODO: Correctly get source of package download
	R: httpx.Response = httpx.post("http://localhost:7040/v1/Download", headers=HEADERS, json={"Packages": Packages});
	if (R.status_code != 200): Log.Awaited().ERROR(f"Non-OK HTTP Code Received: {R.status_code}"); exit();
	Log.Awaited().OK();



	Log.Stateless(f"Unpickling...");
	Nagisa_Downloads: Type.Nagisa_Downloads = pickle.loads(R.content);
	Log.Awaited().OK();
	return Nagisa_Downloads;