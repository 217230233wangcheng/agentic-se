def is_forward_clear():
    # Placeholder for actual forward clarity check
    return True

def is_left_clear():
    # Placeholder for actual left clarity check
    return True

def is_right_clear():
    # Placeholder for actual right clarity check
    return True

def navigate():
    if is_forward_clear():
        return 'FORWARD'
    elif is_left_clear():
        return 'LEFT'
    elif is_right_clear():
        return 'RIGHT'
    else:
        return 'STOP'