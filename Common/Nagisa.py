from .Globals import *;



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

	oldPackages: list[Type.MikaPackage] = cast(Type.Nagisa_Packages, File.JSON_Read("Nagisa.cache", True))["Packages"] if (File.Exists("Nagisa.cache")) else [];
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