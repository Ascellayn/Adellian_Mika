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



	Sd: argparse.ArgumentParser = S.add_parser("info", help="Get all information about a specified MikaRoll.");
	Sd.add_argument("files", nargs="*", help="List of files to parse information from.");



	A: argparse.Namespace = Parser.parse_args();





	match A.action:
		case "update": Nagisa.Update(); exit(0);





		case "info":
			for pkg in A.files:
				roll: str = f"{OG_DIR}/{pkg}";
				if (not File.Exists(roll)): Log.Error(f"{pkg}: file not found."); continue;



				Log.Info(f"Reading {roll}...");
				MikaRoll_Version: str = TSN_Abstracter.Version([x for x in Mika.Unroll.Roller_Version(roll)]); # pyright: ignore[reportArgumentType]
				MikaRoll_Header: Type.MikaRoll_Header = Mika.Unroll.Header(roll);
				Log.Awaited().OK();



				print(f"MikaRoll Archive - Version {MikaRoll_Version}");
				print("");
				print(f"ID: {MikaRoll_Header['ID']}");
				print(f"Name: {MikaRoll_Header['Name']}");
				print(f"Description: {MikaRoll_Header['Description']}");
				print(f"Version: {TSN_Abstracter.Version(MikaRoll_Header['Version'])}"); # pyright: ignore[reportArgumentType]
				print("");
				print(f"Required by Adellian: {', '.join(MikaRoll_Header['Required'])}");
				print(f"Installed by default on Adellian: {', '.join(MikaRoll_Header['Required'])}");
				print(f"Package conflicts with: {', '.join(MikaRoll_Header['Conflicts'])}");
				print("");

				print("Install Options:")
				for i, opt in enumerate(MikaRoll_Header["Options"], start=1):
					print(f"\t[{i}/{len(MikaRoll_Header["Options"])}] - {opt['Name']}: {opt["Description"]}");
					print(f"\tScripts Folder: {opt['Scripts']['Data']}");
					print(f"\tInstall Script: {opt['Scripts']['Install']}");
					print(f"\tUninstall Script: {opt['Scripts']['Uninstall']}");
					print(f"\tUpdate Script: {opt['Scripts']['Update']}");

				print(f"\n");

			exit(0);





		case "download":
			Nagisa_Downloads: Type.Nagisa_Downloads = Nagisa.Download(A.packages);

			for pkg in Nagisa_Downloads["Packages"].keys():
				if (not Mika.Unroll.Valid(Nagisa_Downloads["Packages"][pkg], False)): continue;
				with open(f"{OG_DIR}/{pkg}.MikaRoll", "w+b") as f:
					f.write(Nagisa_Downloads["Packages"][pkg]);
					Log.Info(f"Downloaded \"{pkg}.MikaRoll\" successfully.");

			exit(0);





	print(f"{App.Name} {TSN_Abstracter.App_Version()} (TSNA {TSN_Abstracter.Version()})");
	Parser.print_help();