"""
Adellian "Mika" Archive Utility
JSON Formatted XZ Compressed Pickle'd File
"""
from TSN_Abstracter import *;
import pickle, lzma;
from typing import Literal;



type Adellian_Branches = Literal["Eleison", "Kyrie", "Server"];





class Package_Scripts(TypedDict):
	Data: str;
	Install: str;
	Uninstall: str;
	Update: str | None;



class Package_Option(TypedDict):
	Scripts: Package_Scripts;
	Name: str;
	Description: str;



class MikaPackage(TypedDict):
	""" Adellian .MikaPackage JSON Format"""
	ID: str;
	Type: Literal["Adellian", "Debian"];
	Name: str;
	Description: str;
	Version: tuple[int, ...] | None;
	Required: list[Literal[Adellian_Branches]];
	Default: list[Literal[Adellian_Branches]];
	Dependencies: list[str];
	Conflicts: list[str];
	Options: list[Package_Option];
	Data: tuple[list[str], list[str]];



class MikaArchive(TypedDict):
	_VERSION: tuple[int, int, int];
	Package: MikaPackage;
	Scripts: dict[str, bytes];
	Data: dict[str, bytes];





def __Read(P: str) -> bytes:
	with open(P, "r+b") as F: return F.read();



def __Write(P: str, D: bytes) -> None:
	File.Path_Require(P);
	with open(P, "w+b") as F: F.write(D);



def __Archiver(BASE: str, P: str = ".", MikaArchive: dict[str, Any] = {}) -> dict[str, bytes]:
	T: File.Folder_Contents = File.List(BASE);

	for f in T[1]: MikaArchive[f"{P}/{f}"] = __Read(f"{BASE}/{f}");
	for f in T[0]:
		for m in __Archiver(f"{BASE}/{f}", f"{P}/{f}").items():
			MikaArchive[m[0]] = m[1];

	return MikaArchive;





def Extract(Path: str, Output: str) -> None:
	mikaarchive: MikaArchive = pickle.loads(lzma.decompress(__Read(Path), lzma.FORMAT_XZ));
	File.Path_Require(f"{Output}/.adellian/");
	File.JSON_Write(f"{Output}/.adellian/Adellian.mpkg", mikaarchive["Package"]);
	for f in mikaarchive["Data"].items():
		__Write(f"{Output}/{f[0][2:]}", f[1]);