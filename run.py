services:
  - type: web
    name: fenix-coin-web
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run.py
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: BOT_TOKEN
        sync: false
      - key: WEBAPP_URL
        sync: false
      - key: BOT_USERNAME
        sync: false
      - key: ADMIN_IDS
        sync: false
      - key: START_BALANCE
        value: '1000'
      - key: REF_REWARD
        value: '600'
      - key: MIN_BET
        value: '10'
      - key: MAX_BET
        value: '100000'
  - type: worker
    name: fenix-coin-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.bot
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: BOT_TOKEN
        sync: false
      - key: WEBAPP_URL
        sync: false
      - key: BOT_USERNAME
        sync: false
      - key: ADMIN_IDS
        sync: false
