from services.network_service import check_internet

class AiService:
    def __init__(self):
        pass
    
    def is_online(self):
        return check_internet()
