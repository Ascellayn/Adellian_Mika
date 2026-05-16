from TSN_Abstracter import *;
from TSN_Abstracter import TUI;
import httpx, os, shutil;
import pickle;

from . import Type;





HEADERS: dict[str, str] = {"User-Agent": f"Adellian_Mika/{TSN_Abstracter.App_Version()} (+https://github.com/Ascellayn/Adellian_Mika)"};
OG_DIR: str = os.getcwd();