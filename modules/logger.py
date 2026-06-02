"""
Módulo de logging do projeto Site Workflow v2.2.
Configura loggers com saída para console (Rich) e arquivo.
"""

import logging
from pathlib import Path
from rich.logging import RichHandler


def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    Configura um logger com handlers para console e arquivo.
    
    Args:
        name: Nome do logger (geralmente __name__).
        log_file: Caminho para o arquivo de log.
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        Logger configurado com handlers apropriados.
    """
    # Converter nível de string para constante logging
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Evitar duplicação de handlers se já estiver configurado
    if logger.handlers:
        return logger
    
    # Handler para console com Rich
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True
    )
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Handler para arquivo
    # Garantir que o diretório do log existe
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
