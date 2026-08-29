import random,secrets
def mines(size=5,mine_count=5):
    return set(random.sample(range(size*size),mine_count))
def crash_point():
    r=max(.0001,secrets.randbits(53)/(1<<53))
    return max(1.01,round((1-r)**-1*.97,2))
def roulette(): return random.randint(0,36)
def slots(): return random.choice(["🍒🍒🍒","🍋🍋🍋","7️⃣7️⃣7️⃣","🍒🍋7️⃣","🔔🔔🔔"])
def pve():
    a,b=random.randint(1,100),random.randint(1,100)
    return a,b,a>=b
