# Config cache for optimization
_config_cache = None
_config_mtime = 0

def cargar_config():
    """
    Carga la configuración desde config.json con caché.
    Retorna:
        - lista_blanca: procesos ignorados en ajustes de prioridad
        - lista_ignorados: procesos que NO se deben cerrar por inactividad
        - lista_juegos: lista de juegos
    """
    global _config_cache, _config_mtime
    
    if not os.path.exists(NOMBRE_ARCHIVO_CONFIG):
        return set(), set(), set()
    
    try:
        current_mtime = os.path.getmtime(NOMBRE_ARCHIVO_CONFIG)
        if _config_cache is None or current_mtime > _config_mtime:
            with open(NOMBRE_ARCHIVO_CONFIG, "r") as f:
                datos = json.load(f)
                _config_cache = datos
                _config_mtime = current_mtime
        
        lista_blanca = set(item.lower() for item in _config_cache.get("lista_blanca", []))
        lista_ignorados = set(item.lower() for item in _config_cache.get("ignorar", []))
        lista_juegos = set(item.lower() for item in _config_cache.get("juegos", []))
        return lista_blanca, lista_ignorados, lista_juegos
    except (IOError, OSError, PermissionError) as e:
        print(f"Error de archivo config: {e}")
        return set(), set(), set()
    except json.JSONDecodeError as e:
        print(f"Error JSON en config: {e}")
        return set(), set(), set()
    except Exception as e:
        print(f"Error inesperado cargando config: {e}")
        return set(), set(), set()