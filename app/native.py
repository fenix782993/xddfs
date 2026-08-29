EMOJI={"dice":"🎲","darts":"🎯","football":"⚽","basketball":"🏀","bowling":"🎳","slots":"🎰"}
def win(kind,value):
    if kind=="slots": return value in {1,22,43,64}
    return value=={"dice":6,"darts":6,"football":5,"basketball":5,"bowling":6}.get(kind,6)
