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
from typing import Literal;





# MikaRoll Header
MIKAROLLER_VERSION: tuple[int, int, int] = (1,0,0);
MIKAROLL_SIGNATURE: bytes = "MikaRoll".encode("ASCII");
MIKAROLL_VERSION: bytes = b"".join([x.to_bytes(1, "little") for x in MIKAROLLER_VERSION]);
MIKAROLL_RESERVED: bytes = b"\xFF\xFF\xFF"





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










# Util Functions
def Roll(Path: str, Output: str, MikaPackage: str | MikaRoll_Header, Option: str) -> None:
	""" Creates a new MikaRoll Archive. """
	Log.Info(f"Mika Roller Utility - {TSN_Abstracter.Version(MIKAROLLER_VERSION)}");
	Log.Stateless(f"Rolling {Output}...");
	Log.Stateless(f"Reading MikaPackage...");
	if (not isinstance(MikaPackage, str)): HEADER: MikaRoll_Header = MikaPackage;
	else:
		p: str = f"{Path}/.adellian/{MikaPackage}";
		if (not File.Exists(p)): raise FileNotFoundError(f"MikaPackage \"{Path}/.adellian/{MikaPackage}\" does not exist.");
		HEADER: MikaRoll_Header = cast(MikaRoll_Header, File.JSON_Read(p)); del p;
	del MikaPackage;
	Log.Awaited().OK();



	Log.Stateless(f"Validating MikaPackage...");
	# Option Verification
	pkgopt: MikaRoll_PKGOpt | None = None;
	for opt in HEADER["Options"]:
		if (opt["Name"] == Option): pkgopt = opt; break;
	if (not pkgopt): raise Not_Found(f"Option \"{Option}\" not found.");
	HEADER["Options"] = [pkgopt];
	del Option; del pkgopt;
	Log.Awaited().OK();





	Log.Stateless(f"Adding Cutlery...");
	scripts: dict[str, bytes] = __Archiver(f"{Path}/.adellian/{HEADER['Options'][0]['Scripts']['Data']}/");
	Log.Awaited().OK(f"{len(scripts.keys())} files");



	Log.Stateless(f"Cooking Roll...");
	archive: dict[str, bytes] = {};
	for f in HEADER["Data"][0]: archive = archive | __Archiver(f"{Path}/{f}", f"./{f}"); # Folders
	for f in HEADER["Data"][1]: archive[f"./{f}"] = __Read(f"{Path}/{f}"); # Files
	Log.Awaited().OK(f"{len(archive.keys())} files");






	Log.Stateless(f"Wrapping Roll...");
	MikaData: bytes = pickle.dumps({
		"Scripts": scripts,
		"Data": archive
	});
	size_uncompressed: float = round(len(MikaData) / 1024, 2);
	Log.Awaited().OK(f"{size_uncompressed}KiB - Uncompressed");
	del scripts; del archive;



	Log.Stateless(f"Packaging Roll...");
	MikaData = lzma.compress(MikaData, format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME);
	size_compressed: float = round(len(MikaData) / 1024, 2);
	Log.Awaited().OK(f"{size_compressed}KiB - Compressed ({-100 + (round((size_compressed / size_uncompressed) * 100, 2))}%)");
	del size_compressed; del size_uncompressed;


	Log.Stateless(f"Labeling Roll...");
	MikaHeader: bytes = lzma.compress(json.dumps(HEADER).encode("utf-8"), format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME);
	if (len(MikaHeader) > 65536): raise OverflowError(f"MikaHeader is over 64KiB in size! ({len(MikaHeader)} Bytes)");
	Log.Awaited().OK();

	Log.Stateless(f"Shipping Roll...");
	with open(Output, "w+b") as f: f.write(b"");
	with open(Output, "a+b") as MikaRoll:
		MikaRoll.write(MIKAROLL_SIGNATURE + MIKAROLL_VERSION + len(MikaHeader).to_bytes(2, "little") + MIKAROLL_RESERVED + MikaHeader);
		del MikaHeader;
		MikaRoll.write(MikaData);
		del MikaData;
	Log.Awaited().OK();
	Log.Awaited().OK(); # Don't forget the first awaited





class Unroll:
	@staticmethod
	def Get(Wildcard: str | bytes) -> bytes:
		match Wildcard:
			case str():
				with open(Wildcard, "r+b") as f:
					return f.read();
			case bytes(): return Wildcard;



	@staticmethod
	def Roller_Version(MikaRoll: bytes) -> bytes:
		return MikaRoll[8:11];



	@staticmethod
	def Valid(MikaRoll: bytes, Raise: bool = True) -> bool:
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
	def Header_Size(MikaRoll: bytes) -> int:
		return int.from_bytes(MikaRoll[11:13], "little");



	@staticmethod
	def Header(MikaRoll: str | bytes) -> MikaRoll_Header:
		MikaRoll = Unroll.Get(MikaRoll);
		return json.loads(
			lzma.decompress(
				MikaRoll[16 : Unroll.Header_Size(MikaRoll)+16],
				lzma.FORMAT_XZ
			)
		);