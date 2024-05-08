from configparser import ConfigParser
import string

def remove_space(str):
    return str.replace(' ', '')

class FrameConfig():
    def __init__(self, name, identifier, payload):
        self.name = name
        self.identifier = identifier
        self.payload = payload

class MyConfigParser():
    def get_frame_config(self, filename):
        conf = ConfigParser()  
        conf.read(filename)
        frame_configs = dict()
        for section_name in conf.sections():
            payload_str = conf.get(section_name, 'payload', fallback='')
            identifier = conf.get(section_name, 'id', fallback='')
            payload_str = remove_space(payload_str)

            payload = []
            if len(payload_str) > 0:
                payload = payload_str.split(",", 8)

            fc = FrameConfig(section_name, identifier, payload)
            frame_configs[section_name] = fc
        return frame_configs
    
    def get_frame_parser_config(self, filename):
        conf = ConfigParser()  
        conf.read(filename)
        parser_configs = dict()
        for section_name in conf.sections():
            section_config = dict()
            for key in conf[section_name].keys():
                print(f's={section_name}, key={key}, value={conf[section_name][key]}')

                mast_str = remove_space(conf[section_name][key])
                mask_str_list = []
                if len(mast_str) > 0:
                    mask_str_list = mast_str.split(",", 8)
                
                section_config[key] = mask_str_list
            parser_configs[section_name] = section_config
        return parser_configs


if __name__ == "__main__":
    try:
        parser = MyConfigParser()
        frame_configs = parser.get_frame_config('database_tx.ini')
        for s in frame_configs:
            identifier = frame_configs[s].identifier
            payload = frame_configs[s].payload
            name = frame_configs[s].name

            print(f's={s}, {type(s)}, identifier={identifier}, name={name}, payload={payload}')
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt ...')
    print('exit')