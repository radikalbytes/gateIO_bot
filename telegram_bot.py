#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8

from gateAPI import GateIO
import telebot # Importamos las librería
from telebot import types
import json
import numpy as np
from time import sleep, time
from threading import Thread

TOKEN = 'YOUR BOT TOKEN HERE' # Ponemos nuestro Token generado con el @BotFather
bot = telebot.TeleBot(TOKEN) # Combinamos la declaración del Token con la función de la API
lastTime = time()
# 填写 APIKEY APISECRET
apikey = 'YOUR gate.io API key'
secretkey = 'YOUR gate.io API secret key'
API_URL = 'data.gate.io'

gate = GateIO(API_URL,apikey,secretkey)
mimovil_id = 5604615

commands = {  # command description used in the "help" command
              '/start': 'Empezar a usar el bot',
              '/help': 'Comandos de ayuda',
              'balance': 'Balance de monedas',
              'valores': 'Cotizaciones',
              '/list':'Listado monedas',
              'addb <coin>':'Añade par BTC',
              'adde <coin>':'Añade par ETH',
              'addu <coin>':'Añade par USDT',
              'subb <coin>':'Elimina par BTC',
              'sube <coin>':'Elimina par ETH',
              'subu <coin>':'Elimina par USDT'
}
try:
    f = open("users.py","r")
    knownUsers = eval(f.read())
    f.close()
except:
    print("No hay usuarios definidos")
    knownUsers = dict()
    knownUsers = {'usuarios':[]}
    f = open ("users.py","w")
    f.write (str(knownUsers))
    f.close()

file = open('gate_pairs.py','w')
pairs = gate.pairs()
print (str(pairs), end="", file = file)
file.close()

file = open("coin_names.py","r")
coin_names = eval(file.read())
file.close()

def new_user(cid):
    global knownUsers
    dict_tmp = {'user_id':cid,'interval':300,'lasttime':0,'coin':[]}
    knownUsers['usuarios'].append(dict_tmp)
    save_knownusers()

def save_knownusers():
    global knownUsers
    f = open ("users.py","w")
    f.write (str(knownUsers))
    f.close()

def inicia_timers():
    global knownUsers
    for usuario in knownUsers['usuarios']:
        usuario['lasttime'] = time();
    save_knownusers()

def envia_telegram (user_id,mensaje):
    bot.send_message(user_id,mensaje)

def envia_cotizaciones (cid):
    global knownUsers
    try:
        for usuario in knownUsers['usuarios']:
            if usuario['user_id'] == cid:
                enviaPrecio = "Mercado:\n"
                for monedas in usuario['coin']:
                    precio = (gate.ticker(monedas))
                    name = coin_names[monedas]
                    if monedas[-1]=='c':
                        sufix = 'B '
                    elif monedas[-1]=='h':
                        sufix = 'E '
                    elif monedas[-1]=='t':
                        sufix = 'UST '
                    if precio ['result']=='true':
                        enviaPrecio += name + "(" + monedas + "): " + str(precio['last']) + sufix + str(precio['percentChange'])[:6]+"%\n"
                envia_telegram(cid,enviaPrecio)
    except:
        print("Fallo al enviar-recibir cotizaciones")

def controlPrecios ():
    global knownUsers
    while (1):
        for usuario in knownUsers['usuarios']:
            intervalo = usuario['interval']
            timepassed = usuario['lasttime']
            if ((time()-timepassed)>intervalo) :
                usuario['lasttime'] = time()
                envia_cotizaciones(usuario['user_id'])

def agrega_moneda(cid_,moneda_):
    global pairs
    if moneda_ in pairs:
        for key in knownUsers['usuarios']:
            if key['user_id'] == cid_:
                key['coin'].append(moneda_)
                save_knownusers()
                break
    else:
        r_ = moneda_ + " no existe en gate.io"
        bot.send_message(cid_,r_)

def borra_moneda(cid_,moneda_):
    global pairs
    if moneda_ in pairs:
        for key in knownUsers['usuarios']:
            if key['user_id'] == cid_:
                if moneda_ in key['coin']:
                    key['coin'].remove(moneda_)
                    save_knownusers()
                    break
                else:
                    r_ = moneda_ + " no está en tu lista"
                    bot.send_message(cid_,r_)
    else:
        r_ = moneda_ + " no existe en gate.io"
        bot.send_message(cid_,r_)


insultos = []
f = open("insultos.py")
for linea in f:
    insultos.append(linea[:-1].lower())
subproceso = Thread(target=controlPrecios)
subproceso.start()
inicia_timers()

# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(m):
    global knownUsers
    nuevo=1
    cid = m.chat.id
    for usuario in knownUsers['usuarios']:
        if cid == usuario['user_id']:
            bot.send_message(cid, "Ya nos conocemos!... sobran las presentaciones")
            nuevo=0
            break
    if nuevo == 1:  # if user hasn't used the "/start" command yet:
        #knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        bot.send_message(cid, "Hola melón, déjame que te vea...")
        bot.send_message(cid, "Me quedo con tu cara... ya no te olvido")
        command_help(m)  # show the new user the help page
        new_user(cid)
@bot.message_handler(commands=['list'])
def command_list(m):
    cid = m.chat.id
    bot.send_message(cid, str(pairs))

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "Comandos de ayuda: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += key + ": "
        help_text += commands[key] + "\n"
    help_text += "Y no olvides que está prohibido insultar\n"
    bot.send_message(cid, help_text)  # send the generated help page

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    cid = message.chat.id
    global intervalo
    lista = ''
    #global balances
    if message.text.lower()=='balance':
        for usuario in knownUsers['usuarios']:
            if cid == usuario['user_id']:
                balances = json.loads(gate.balances())
                if balances ['result']=='true':
                    for key in balances['available']:
                        linea = (str(key)+":"+str(balances['available'][key]))
                        lista += linea + '\n'
                    lista += "Locked:\n"
                    for key in balances['locked']:
                        linea = (str(key)+":"+str(balances['locked'][key]))
                        lista += linea + '\n'
                envia_telegram(cid, lista)
            else:
                envia_telegram(cid, "Lo siento amigo, pero no te conozco!!!")

    for insulto in insultos:
        if message.text.lower()==insulto:
            envia_telegram(cid, 'Tu puta madre, mono!')

    if message.text.lower()=='time':
        for usuario in knownUsers['usuarios']:
            if cid == usuario['user_id']:
                intervalo_ = str(usuario['interval'])
                envia_telegram(cid, 'Tiempo de notificación: ' + intervalo_)
                break

    if message.text.lower()[:4]=='time':
        try:
            intervalo = float(str(message.text)[4:])
            for usuario in knownUsers['usuarios']:
                if cid == usuario['user_id']:
                    usuario['interval'] = intervalo
                    save_knownusers()
                    envia_telegram(cid, 'Tiempo de notificación: ' + str(intervalo) + " seg" )
                    break
        except:
            pass

    if message.text.lower()=='valores':
        envia_cotizaciones(cid)

    if message.text.lower()[:4]=='addb':
        moneda = message.text.lower()[5:] + "_btc"
        agrega_moneda(cid,moneda)

    if message.text.lower()[:4]=='adde':
        moneda = message.text.lower()[5:] + "_eth"
        agrega_moneda(cid,moneda)

    if message.text.lower()[:4]=='addu':
        moneda = message.text.lower()[5:] + "_usdt"
        agrega_moneda(cid,moneda)

    if message.text.lower()[:4]=='subb':
        moneda = message.text.lower()[5:] + "_btc"
        borra_moneda(cid,moneda)

    if message.text.lower()[:4]=='sube':
        moneda = message.text.lower()[5:] + "_eth"
        borra_moneda(cid,moneda)

    if message.text.lower()[:4]=='subu':
        moneda = message.text.lower()[5:] + "_usdt"
        borra_moneda(cid,moneda)

while True:
    try:
        bot.polling(none_stop=True)
        # ConnectionError and ReadTimeout because of possible timout of the requests library
        # TypeError for moviepy errors
        # maybe there are others, therefore Exception
    except Exception as e:
        sleep(15)
