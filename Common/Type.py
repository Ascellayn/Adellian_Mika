from typing import TypedDict, Literal;





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










class Nagisa_Packages(TypedDict):
	Last_Update: int;
	Error: list[str];
	Packages: list[MikaRoll_Header];



class Nagisa_Files(TypedDict):
	File: str;
	Data: bytes;



class Nagisa_Downloads(TypedDict):
	Error: list[str];
	Packages: dict[str, bytes];










class Request_Download(TypedDict):
	Packages: list[tuple[str, str]];