from Common import *;
import argparse;



if (__name__ == "__main__"):
	os.chdir(File.Main_Directory);
	TSN_Abstracter.Require_Version(App.TSNA);
	Parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=App.Name, description=App.Description, usage="apm [action] [arguments]", epilog="Remember to hug a Mika a day~");

	S: argparse._SubParsersAction = Parser.add_subparsers(dest="action");
	S.add_parser("update", help="Update list of known installable-packages");

	Sd: argparse.ArgumentParser = S.add_parser("download", help="Download a raw .MikaArchive of specific package.");
	Sd.add_argument("packages", nargs="*", help="List of packages to download. Format {ID}¤{Option}, if only {ID} is provided, you will be prompted to make a choice.");
	A: argparse.Namespace = Parser.parse_args();

	match A.action:
		case "update":
			Nagisa.Update(); exit(0);



		case "download":
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
			for pkg in A.packages:
				if ("¤" in pkg): Packages.append(pkg.split("¤", 1)); continue;
				Packages.append([pkg]);

			# Validate against cache
			for i, pkg in enumerate(Packages):
				if (pkg[0] not in PKGs.keys()): Log.Critical(f"Package \"{pkg[0]}\" does not exist."); exit(1);
				if (len(pkg) == 1):
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



			Log.Stateless(f"Downloading packages...");
			R: httpx.Response = httpx.post("http://localhost:7040/v1/Download", headers=HEADERS, json={"Packages": Packages});
			if (R.status_code != 200): Log.Awaited().ERROR(f"Non-OK HTTP Code Received: {R.status_code}"); exit();
			Log.Awaited().OK();



			Log.Stateless(f"Unpickling...");
			Nagisa_Downloads: Type.Nagisa_Downloads = pickle.loads(R.content);
			Log.Awaited().OK();

			for pkg in Nagisa_Downloads["Packages"].keys():
				if (not Mika.Unroll.Valid(Nagisa_Downloads["Packages"][pkg])): continue;
				with open(f"{OG_DIR}/{pkg}.MikaRoll", "w+b") as f:
					f.write(Nagisa_Downloads["Packages"][pkg]);
					Log.Info(f"Downloaded \"{pkg}.MikaRoll\" successfully.");
				print(Mika.Unroll.Header(Nagisa_Downloads["Packages"][pkg]));

			exit(0);

	print(f"{App.Name} {TSN_Abstracter.App_Version()} (TSNA {TSN_Abstracter.Version()})");
	Parser.print_help();