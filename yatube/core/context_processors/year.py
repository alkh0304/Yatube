from datetime import datetime


def year(request):
    Cyear = datetime.now().year
    return {'year': Cyear}
