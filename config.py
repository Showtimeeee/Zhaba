EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_from': 'your_email@gmail.com',
    'email_password': 'your_app_password',
    'email_to': 'recipient@example.com',
}


WEBSOCKET_CONFIG = {
    'host': 'localhost', 
    'port': 8765,       
    'max_connections': 100,  
}


APP_CONFIG = {
    'debug': True,           
    'max_message_size': 1024, 
}


LOGGING_CONFIG = {
    'log_file': 'zhaba.log',       
    'log_level': 'DEBUG',             
    'max_bytes': 10 * 1024 * 1024,   
    'backup_count': 5,         
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}
