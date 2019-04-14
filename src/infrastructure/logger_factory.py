import logging
from logging.config import fileConfig

class LoggerFactory:
    @staticmethod
    def create_logger(name, correlation_id: str =''):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('./logs/{0}{1}.log'.format(name, '_' + correlation_id if correlation_id else ''))
        fh.setLevel(logging.INFO)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('{0}%(asctime)s - %(name)s - %(levelname)s - %(message)s'.format('[%s] ' 
                                    % correlation_id if correlation_id else ''))
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger
