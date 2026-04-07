from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(func):           # custom decorator to check admin role , will be used with buildings, floors and rooms page access
    
    @wraps(func)
    def wrapper(*args, **kwargs):

        if current_user.role != "admin":
            flash("Access denied", "error")
            return redirect(url_for("user.dashboard"))        # not admin - deny access #return redirect(url_for("user.dashboard")) - not admin - redirect
        
        return func(*args, **kwargs)                                # admin - run original function
    
                                                # wrapper.__name__ = func.__name__  set wrapper name to original func name(manually without @wraps)
    return wrapper                                           # runs after decorator is applied not after all the above conditions
