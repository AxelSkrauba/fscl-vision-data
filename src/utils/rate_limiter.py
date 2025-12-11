"""
Rate limiter para respetar limites de la API de iNaturalist.
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional


class RateLimiter:
    """
    Rate limiter thread-safe con limites por minuto y por dia.
    
    Implementa espera automatica cuando se alcanzan los limites,
    con backoff exponencial para errores 429.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        requests_per_day: int = 10000,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el rate limiter.
        
        Args:
            requests_per_minute: Maximo de requests por minuto (default: 100)
            requests_per_day: Maximo de requests por dia (default: 10000)
            logger: Logger opcional para mensajes
        """
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        self.request_times: list = []
        self.daily_count = 0
        self.daily_reset = datetime.now() + timedelta(days=1)
        self.lock = threading.Lock()
        self.logger = logger or logging.getLogger(__name__)
    
    def wait_if_needed(self) -> None:
        """
        Espera si es necesario para respetar los limites de rate.
        
        Este metodo debe llamarse antes de cada request a la API.
        Bloquea el thread actual si se han alcanzado los limites.
        """
        with self.lock:
            now = datetime.now()
            
            if now > self.daily_reset:
                self.daily_count = 0
                self.daily_reset = now + timedelta(days=1)
                self.request_times = []
                self.logger.debug("Daily limit reset")
            
            if self.daily_count >= self.rpd:
                sleep_time = (self.daily_reset - now).total_seconds()
                if sleep_time > 0:
                    self.logger.warning(
                        f"Daily limit ({self.rpd}) reached. "
                        f"Sleeping {sleep_time:.0f}s until reset."
                    )
                    time.sleep(min(sleep_time, 3600))
                    self.daily_count = 0
                    self.daily_reset = datetime.now() + timedelta(days=1)
            
            one_minute_ago = now - timedelta(minutes=1)
            self.request_times = [
                t for t in self.request_times if t > one_minute_ago
            ]
            
            if len(self.request_times) >= self.rpm:
                oldest_in_window = min(self.request_times)
                sleep_time = 60 - (now - oldest_in_window).total_seconds()
                if sleep_time > 0:
                    self.logger.debug(
                        f"Minute limit ({self.rpm}) reached. "
                        f"Sleeping {sleep_time:.1f}s"
                    )
                    time.sleep(sleep_time + 0.1)
            
            self.request_times.append(datetime.now())
            self.daily_count += 1
    
    def handle_rate_limit_error(self, retry_after: Optional[int] = None) -> None:
        """
        Maneja un error 429 (Too Many Requests) de la API.
        
        Args:
            retry_after: Segundos a esperar (del header Retry-After).
                        Si None, usa 60 segundos por defecto.
        """
        sleep_time = retry_after if retry_after is not None else 60
        self.logger.warning(
            f"Rate limit error (429). Sleeping {sleep_time}s"
        )
        time.sleep(sleep_time)
    
    def get_stats(self) -> dict:
        """
        Retorna estadisticas del rate limiter.
        
        Returns:
            Dict con estadisticas actuales
        """
        with self.lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_requests = len([
                t for t in self.request_times if t > one_minute_ago
            ])
            
            return {
                'requests_last_minute': recent_requests,
                'requests_today': self.daily_count,
                'rpm_limit': self.rpm,
                'rpd_limit': self.rpd,
                'rpm_remaining': max(0, self.rpm - recent_requests),
                'rpd_remaining': max(0, self.rpd - self.daily_count),
                'daily_reset_in_seconds': (self.daily_reset - now).total_seconds()
            }
