"""
Adellian "Mika" Archive Utility
JSON-ish Formatted XZ Compressed Pickle'd File


## MikaRoll Archive File Format
```hex
4D 69 6B 61 52 6F 6C 6C     # File Signature ("MikaRoll")
XX XX XX                    # MikaRoll Version (append each byte as a Little Endian int)
         YY YY              # Size of MikaRoll Header (Max 64KiB) - (stored in Little Endian)
               ?? ?? ??     # Reserved Bytes for future versions
7zXZ{MikaRoll_Header}       # 7zXZ Compressed MikaRoll Header
7zXZ{Pickle(MikaRoll_Data)} # MikaRoll Data, Pickle'd and then 7zXZ Compressed
```
"""
from TSN_Abstracter import *;
import pickle, lzma, json;
from typing import Literal, Optional;





# MikaRoll Header
MIKAROLLER_VERSION: tuple[int, int, int] = (1,1,0);
MIKAROLL_SIGNATURE: bytes = "MikaRoll".encode("ASCII");
MIKAROLL_VERSION: bytes = b"".join([x.to_bytes(1, "little") for x in MIKAROLLER_VERSION]);
MIKAROLL_RESERVED: bytes = b"\xFF\xFF\xFF";





# MikaRoll Data Format
type Adellian_Branches = Literal["Eleison", "Kyrie", "Server"];



class MikaRoll_PKGSrc(TypedDict):
	Data: str;
	Install: str;
	Uninstall: str;
	Update: str | None;



class MikaRoll_PKGOpt(TypedDict):
	Scripts: MikaRoll_PKGSrc;
	Name: str;
	Description: str;



class MikaRoll_Header(TypedDict):
	""" Adellian .MikaRoll JSON Format"""
	ID: str;
	Type: Literal["Adellian", "Debian"];
	Name: str;
	Description: str;
	Version: tuple[int, ...] | None;
	Required: list[Literal[Adellian_Branches]];
	Default: list[Literal[Adellian_Branches]];
	Dependencies: list[str];
	Conflicts: list[str];
	Options: list[MikaRoll_PKGOpt];
	Data: tuple[list[str], list[str]];
	Contains: Optional[list[int]]; # 1st number is amount of Script files, 2nd is Data files.
	Source: Optional[str];



class MikaRoll_Data(TypedDict):
	Scripts: dict[str, bytes];
	Data: dict[str, bytes];





# Helper Functions / Classes
class Not_Found(Exception): ...;



def __Read(P: str) -> bytes:
	with open(P, "r+b") as F: return F.read();



def __Write(P: str, D: bytes) -> None:
	File.Path_Require(P);
	with open(P, "w+b") as F: F.write(D);





def __Archiver(BASE: str, P: str = ".", MikaArchive: dict[str, bytes] | None = None) -> dict[str, bytes]:
	if (not MikaArchive): MikaArchive = {};
	T: File.Folder_Contents = File.List(BASE + "/");

	for f in T[1]: MikaArchive[f"{P}/{f}"] = __Read(f"{BASE}/{f}");
	for f in T[0]: MikaArchive = MikaArchive | __Archiver(f"{BASE}/{f}", f"{P}/{f}");

	return MikaArchive;



def __ArchiverLS(BASE: str, P: str = ".", MikaArchive: int | None = None) -> int:
	if (not MikaArchive): MikaArchive = 0;
	T: File.Folder_Contents = File.List(BASE + "/");

	MikaArchive += len(T[1]);
	for f in T[0]: MikaArchive += __ArchiverLS(f"{BASE}/{f}", f"{P}/{f}");

	return MikaArchive;










# Util Functions
def Roll(Path: str, Output: str, MikaPackage: str | MikaRoll_Header, Option: str, Source: str) -> None:
	""" Creates a new MikaRoll Archive. """
	LogPrefix: str = f"{String.ASCII.Text.Bold}{Output}{String.ASCII.Text.Reset} |";
	Log.Info(f"Mika Roller Utility - {TSN_Abstracter.Version(MIKAROLLER_VERSION)}");
	Log.Stateless(f"{LogPrefix} Rolling {Output}...");
	Log.Stateless(f"{LogPrefix} Reading MikaPackage...");
	if (not isinstance(MikaPackage, str)): mr_header: MikaRoll_Header = MikaPackage;
	else:
		p: str = f"{Path}/.adellian/{MikaPackage}";
		if (not File.Exists(p)): raise FileNotFoundError(f"MikaPackage \"{Path}/.adellian/{MikaPackage}\" does not exist.");
		mr_header: MikaRoll_Header = cast(MikaRoll_Header, File.JSON_Read(p)); del p;
	del MikaPackage;
	Log.Awaited().OK();



	Log.Stateless(f"{LogPrefix} Validating MikaPackage...");
	# Option Verification
	pkgopt: MikaRoll_PKGOpt | None = None;
	for opt in mr_header["Options"]:
		if (opt["Name"] == Option): pkgopt = opt; break;
	if (not pkgopt): raise Not_Found(f"Option \"{Option}\" not found.");
	mr_header["Options"] = [pkgopt];
	del Option; del pkgopt;
	Log.Awaited().OK();





	Log.Stateless(f"{LogPrefix} Adding Cutlery...");
	scripts: dict[str, bytes] = __Archiver(f"{Path}/.adellian/{mr_header['Options'][0]['Scripts']['Data']}/");
	Log.Awaited().OK(f"{len(scripts.keys())} files");



	Log.Stateless(f"{LogPrefix} Cooking Roll...");
	archive: dict[str, bytes] = {};
	for f in mr_header["Data"][0]: archive = archive | __Archiver(f"{Path}/{f}", f"./{f}"); # Folders
	for f in mr_header["Data"][1]: archive[f"./{f}"] = __Read(f"{Path}/{f}"); # Files
	Log.Awaited().OK(f"{len(archive.keys())} files");
	del Path;






	Log.Stateless(f"{LogPrefix} Wrapping Roll...");
	MR_Data: bytes = pickle.dumps({
		"Scripts": scripts,
		"Data": archive
	});
	size_uncompressed: float = round(len(MR_Data) / 1024, 2);
	Log.Awaited().OK(f"{size_uncompressed}KiB - Uncompressed");
	mr_header["Contains"] = [len(scripts), len(archive)];
	mr_header["Source"] = Source;
	del scripts; del archive;



	Log.Stateless(f"{LogPrefix} Packaging Roll...");
	MR_Data = lzma.compress(MR_Data, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME);
	size_compressed: float = round(len(MR_Data) / 1024, 2);
	Log.Awaited().OK(f"{size_compressed}KiB - Compressed ({-100 + (round((size_compressed / size_uncompressed) * 100, 2))}%)");
	del size_compressed; del size_uncompressed;


	Log.Stateless(f"{LogPrefix} Labeling Roll...");
	MR_Header: bytes = lzma.compress(json.dumps(mr_header).encode("utf-8"), format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME);
	if (len(MR_Header) > 65536): raise OverflowError(f"MikaRoll_Header is over 64KiB in size! ({len(MR_Header)} Bytes)");
	Log.Awaited().OK();
	del mr_header;

	Log.Stateless(f"{LogPrefix} Shipping Roll...");
	with open(Output, "w+b") as f: f.write(b""); # Clear entire file...
	with open(Output, "a+b") as MikaRoll: # Because to save on memory we'll use append.
		MikaRoll.write(MIKAROLL_SIGNATURE + MIKAROLL_VERSION + len(MR_Header).to_bytes(2, "little") + MIKAROLL_RESERVED + MR_Header);
		del MR_Header;
		MikaRoll.write(MR_Data);
		del MR_Data;
	

	Log.Awaited().OK();
	Log.Awaited().OK(); # Don't forget the first awaited



def Roll_Header(Path: str, MikaPackage: str | MikaRoll_Header, Source: str) -> MikaRoll_Header:
	""" Only create the finished header of a MikaRoll, intended to be used only by Nagisa Package Distributor """
	LogPrefix: str = f"{String.ASCII.Text.Bold}{Path}{String.ASCII.Text.Reset} |";
	Log.Info(f"Mika Roller Utility - {TSN_Abstracter.Version(MIKAROLLER_VERSION)}");
	Log.Stateless(f"{LogPrefix} Reading MikaPackage...");
	if (not isinstance(MikaPackage, str)): mr_header: MikaRoll_Header = MikaPackage;
	else:
		p: str = f"{Path}/.adellian/{MikaPackage}";
		if (not File.Exists(p)): raise FileNotFoundError(f"MikaPackage \"{Path}/.adellian/{MikaPackage}\" does not exist.");
		mr_header: MikaRoll_Header = cast(MikaRoll_Header, File.JSON_Read(p)); del p;
	del MikaPackage;
	Log.Awaited().OK();



	archive: int = 0;
	Log.Stateless(f"{LogPrefix} Adding Cutlery...");
	scripts: int = __ArchiverLS(f"{Path}/.adellian/{mr_header['Options'][0]['Scripts']['Data']}/");
	Log.Awaited().OK(f"{scripts} files");



	Log.Stateless(f"{LogPrefix} Cooking Roll...");
	for f in mr_header["Data"][0]: archive = archive | __ArchiverLS(f"{Path}/{f}", f"./{f}"); # Folders
	archive += len(mr_header["Data"][1]); # Files
	Log.Awaited().OK(f"{archive} files");
	del Path;

	mr_header["Contains"] = [scripts, archive];
	mr_header["Source"] = Source;
	return mr_header;










# Unrolling Utils
class Unroll:
	@staticmethod
	def Get(Wildcard: str | bytes, Max: int = -1, Seek: int = -1) -> bytes:
		match Wildcard:
			case str():
				with open(Wildcard, "r+b") as f:
					if (Seek != -1): f.seek(Seek);
					if (Max == -1): return f.read();
					return f.read(Max);
			case bytes():
				if (Seek != -1 and Max != -1): return Wildcard[Seek:Max+Seek];
				if (Seek != -1 and Max == -1): return Wildcard[Seek:];
				if (Seek == -1 and Max != -1): return Wildcard[:Max];
				return Wildcard;



	@staticmethod
	def Roller_Version(MikaRoll: str | bytes) -> bytes:
		return Unroll.Get(MikaRoll, 16)[8:11];



	@staticmethod
	def Valid(MikaRoll: str | bytes, Raise: bool = True) -> bool:
		if (MikaRoll[:8] != MIKAROLL_SIGNATURE):
			msg: str = f"Invalid Signature: {MikaRoll[:8]}";
			if (Raise): raise Exception(msg);
			Log.Error(msg);
			return False;
	
		Roller_Version: bytes = Unroll.Roller_Version(MikaRoll);
		if (Roller_Version[0] != MIKAROLL_VERSION[0]):
			msg: str = f"MikaRoller Utility is out of date! (File is of version \"v{'.'.join([str(x) for x in Roller_Version])}\" but we're running {'.'.join(String.ify_Array(MIKAROLLER_VERSION))}!)";
			if (Raise): raise Exception(msg);
			Log.Error(msg);
			return False;

		return True;



	@staticmethod
	def Header_Size(MikaRoll_Signature: bytes) -> int:
		return int.from_bytes(MikaRoll_Signature[11:13], "little");



	@staticmethod
	def Header(MikaRoll: str | bytes) -> MikaRoll_Header:
		return json.loads(
			lzma.decompress( # Signature → Header Size → Only Header → Decompress → Load JSON
				Unroll.Get(MikaRoll, Unroll.Header_Size(Unroll.Get(MikaRoll, 16)), 16),
				lzma.FORMAT_XZ
			)
		);