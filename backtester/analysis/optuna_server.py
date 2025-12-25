from optuna_dashboard import run_server
from utility.setting import DB_OPTUNA
from utility.static import thread_decorator

@thread_decorator
def RunOptunaServer():
    try:
        run_server(DB_OPTUNA)
    except:
        pass


