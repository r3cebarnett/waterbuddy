import json
import logging
import traceback

log = logging.getLogger('waterbuddy')

class Settings:
    def __init__(self, path):
        self.path = path
        try:
            with open(self.path, 'r') as settings_file:
                self.settings = json.load(settings_file)
        except:
            self.settings = {}
    
    def get(self, primary, secondary=None):
        try:
            ans = self.settings[primary]
            if secondary:
                ans = ans[secondary]
            return ans
        except:
            log.debug(traceback.format_exc())
            return None
    
    def set1(self, primary, payload):
        try:
            self.settings[primary] = payload
            ans = True
        except:
            ans = False
        
        return ans
    
    def set2(self, primary, secondary, payload):
        try:
            self.settings[primary][secondary] = payload
            return True
        except:
            return False
    
    def get_bulk(self):
        return self.settings
    
    def get_bulk_str(self):
        return json.dumps(self.settings, indent=4, separators=(',', ': '))
    
    def set_bulk(self, strdict):
        self.settings = strdict
    
    def save(self):
        try:
            with open(self.path, 'w') as f:
                f.write(self.get_bulk_str())
            return True
        except:
            return False