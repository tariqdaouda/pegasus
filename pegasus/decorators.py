import numpy as np

import functools
import time
import gc
import logging

class TimeLogger:
    """
    Log time spent in a function.
    Can also log an additional custom mesage for debug / info / warning... purposes
    
    Example:
    -------

    @TimeLogger(custom_message="This a warning to be logged at the end", custom_message_type="warning")
    def print_something():
        print("Hello World")    

    """
    
    def __init__(self, custom_message:str=None, custom_message_type:str="debug", verbose=False):
        super(TimeLogger, self).__init__()
        self.custom_message = custom_message
        self.custom_message_type = custom_message_type
        self.verbose = verbose
        self.logger = logging.getLogger("pegasus")

    def __call__(self, function):
        if hasattr(function, "_pg_wrapped") :
            function = function._pg_wrapped
    
        @functools.wraps(function)
        def _do(*args, **kwargs):
            if self.verbose:
                self.logger.info(
                    "Entering: %s" % function.__code__.co_name
                )

            start = time.perf_counter()
            res = function(*args, **kwargs)
            end = time.perf_counter()
            
            self.logger.info(
                "Time spent on '{}' = {:.2f}s.".format(
                    function.__code__.co_name,
                    end - start
                )
            )

            if self.custom_message is not None:
                log_fct = getattr(self.logger, self.custom_message_type)
                log_fct(self.custom_message)
            
            return res

        _do._pg_wrapped = function
        return _do

class GCCollect:
    """
    Force the collection garbage according to a binomial distribution.
    Python's garbage collection is not that automatic. This decorator is
    especially useful for freeing memory after functions that call on modules
    that create a lot intermediary objects.

    Garbage collection is not time consuming. However sometimes you might want to
    decrease the probability of the collection happening when decorating a very
    (very) fast function.
    In most cases the default probability of 1 should be used. 

    Example:
    -------

    @GCCollect()
    def print_something():
        print("Hello World")

    """
    def __init__(self, collection_proba:float=1):
        super(GCCollect, self).__init__()
        self.collection_proba = collection_proba
    
    def __call__(self, function):
        if hasattr(function, "_pg_wrapped") :
            function = function._pg_wrapped

        @functools.wraps(function)
        def _do(*args, **kwargs):
            res = function(*args, **kwargs)
            sample = np.random.binomial(1, self.collection_proba, 1)[0]
            if sample > 0:
                gc.collect()

            return res

        _do._pg_wrapped = function
        return _do
