header = ["mode", "pid", "profile", "paymentMethod", "proxyList"]

def check_errors(task: list, i: int) -> list:
    errors = []
    if "" in task[i].values():
        errors.append("Empty Value(s) in Row")
    if task[i]["mode"].lower() not in ["normal", "preload"]:
        errors.append("Invalid Checkout Mode")
    if len(task[i]["pid"]) != 8 or not task[i]["pid"].isdigit():
        errors.append("Invalid PID Length/Format")
    if task[i]["paymentMethod"].lower() not in ["card", "paypal", "pp", "cc"]:
        errors.append("Invalid Payment Method")
    if None in task[i]:
        if len(task[i][None]) != 0:
            errors.append("Extra Column(s) in Task")
    
    return errors