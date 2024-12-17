import json
import os
import platform
import subprocess
import sys
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk
import shutil

from PIL import Image, ImageTk

from variables import PURPLE, YELLOW, RED, DEFAULT_SETTINGS, ICON, LANG_EN, LANG_PL, LANG_RU


main_script = ['''try:
    import time
    from subprocess import Popen, DETACHED_PROCESS
    from tkinter import TclError, Frame
    from tkinter import messagebox as mb
    import json
    import os
    import re
    from threading import Thread
    import ctypes
    from math import ceil
    import logging
    import sys
    
    import customtkinter as ctk
    import pyperclip

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
except Exception as error:
    # with open('debug.log', 'a') as log:
    #     log.write(f'{time.strftime("[ %d.%m.%Y | %H:%M:%S ]", time.localtime())}: Raised {error.__class__}: {error}')
    mb.showerror('Dpendencies error', 'Reinstall the app or try to contact with the developer.')
    exit(-1)

# disk = os.getWD().split('\\\\')[0]
user = os.getlogin()
notebook_path = f'C:\\\\Users\\\\{user}\\\\AppData\\\\Local\\\\NoteBook1'

logging.basicConfig(filename=f'{notebook_path}\\\\conf\\\\debug.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception


# writes data to the settings file
def write_data():
    with open(f'{notebook_path}\\\\conf\\\\settings.json', 'w', encoding='utf-8') as notes:
        notes.write(json.dumps(settings, indent=4))


# encrypts secrets
def encrypt(message):
    if not message:
        return ''
    # Creation of encryption object
    cipher = Cipher(algorithms.AES(ENC_KEY), modes.CBC(ENC_IV), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Выравнивание (padding) сообщения до кратного размеру блока
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    
    # Шифрование выровненного сообщения
    encrypted_message = encryptor.update(padded_data) + encryptor.finalize()
    
    return encrypted_message


# decrypts secrets
def decrypt(encrypted_message):
    if not encrypted_message:
        return ''
    # Создание объекта расшифрования
    cipher = Cipher(algorithms.AES(ENC_KEY), modes.CBC(ENC_IV), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Расшифрование сообщения
    decrypted_padded_message = decryptor.update(encrypted_message) + decryptor.finalize()
    
    # Удаление выравнивания (unpadding) из расшифрованного сообщения
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_message = unpadder.update(decrypted_padded_message) + unpadder.finalize()
    
    return decrypted_message.decode()


# updates chosen note info like its change date, and its size (as file)
def update_note_info(note_type, chosen):
    if note_type == 'note':
        changed_time = time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{chosen}'))
        date.configure(text=lang['gui']['tCh'][0] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", changed_time))
        if settings['showSize']:
            file_size = os.path.getsize(f'{notebook_path}\\\\notes\\\\notes\\\\{chosen}')
            if file_size // 1_000_000 >= 1:
                size_lbl.configure(text=str(round(file_size / 1_000_000, 1)) + ' ' + lang['gui']['not']['szLett'][2])
            elif file_size // 1000 >= 1:
                size_lbl.configure(text=str(round(file_size / 1000, 1)) + ' ' + lang['gui']['not']['szLett'][1])
            else:
                size_lbl.configure(text=str(round(file_size, 1)) + ' ' + lang['gui']['not']['szLett'][0])
    elif note_type == 'secret':
        changed_time = time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{chosen}'))
        secret_date.configure(text=lang['gui']['tCh'][0] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", changed_time))


# saves chosen note's text
def save(event=None):
    if switch.get() == lang['gui']['avTabs'][0]:
        if mb.askyesno(lang['mb']['que']['saveConf'][0], f"{lang['mb']['que']['saveConf'][1]} {bas_current}?"):
            with open(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}', 'w', encoding='utf-8') as note:
                note.write(tb.get('0.0', 'end')[:-1])
            load_chapters(tb.get('0.0', 'end')[:-1])
            update_note_info('note', bas_current)
        else:
            return
        sorting('basic')
    elif switch.get() == lang['gui']['avTabs'][1]:
        if mb.askyesno(lang['mb']['que']['saveConf'][0], f"{lang['mb']['que']['saveConf'][1]} {secret_name.get()}?"):
            chosen = secret_name.get()
            chosen_text = encrypt(secret_tb.get('0.0', 'end')[:-1])
            with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{chosen}', 'wb') as note:
                note.write(chosen_text)
            update_note_info('secret', chosen)
        sorting('secret')


def get_chapters_pattern():
    if settings['chapterPattern'] == '=':
        return re.compile(r'===== ((?!=====).)*? =====')
    elif settings['chapterPattern'] == '>':
        return re.compile(r'>>>>> ((?!<<<<<).)*? <<<<<')
    elif settings['chapterPattern'] == '*':
        return re.compile(r'\\\\*\\\\*\\\\*\\\\*\\\\* ((?!\\\\*\\\\*\\\\*\\\\*\\\\*).)*? \\\\*\\\\*\\\\*\\\\*\\\\*')


# loads chapters to seek to for chosen note's text, if they are
def load_chapters(text):
    global av_chapters
    end_search_index = 0
    av_chapters = {}
    pattern = get_chapters_pattern()
    while True:
        result = re.search(pattern, text[end_search_index:])
        if result:
            chapt_name = text[(result.span()[0]+6+end_search_index):(result.span()[1]-6+end_search_index)]
            av_chapters[chapt_name] = (result.span()[0]+end_search_index, result.span()[1]+end_search_index)
            end_search_index += result.span()[1]
        else:
            break
    if av_chapters:
        l1.pack(side='left')
        chapters_cmb.pack(side='left', ipadx=10, padx=10)
        chapters_cmb.configure(values=av_chapters.keys())
        chapters_cmb.set(lang['gui']['not']['chpts'])
    else:
        try:
            if l1.pack_info() and chapters_cmb.pack_info():
                l1.pack_forget()
                chapters_cmb.pack_forget()
        except TclError:
            pass


def refactor_chapters(new_patt_symb):
    existing_notes = os.listdir(f'{notebook_path}\\\\notes\\\\notes')
    pattern = get_chapters_pattern()
    for note in existing_notes:
        with open(f'{notebook_path}\\\\notes\\\\notes\\\\{note}', 'r') as file:
            text = file.read()
        end_search_index = 0
        while True:
            result: re.Match[str] = re.search(pattern, text[end_search_index:])
            if result:
                text = text[:(end_search_index+result.span()[0])] + (5 * new_patt_symb[0]) + text[(end_search_index+result.span()[0]+5):(end_search_index+result.span()[1]-5)] + (5 * new_patt_symb[1]) + text[(end_search_index+result.span()[1]):]
                end_search_index += result.span()[1]
            else:
                break
        with open(f'{notebook_path}\\\\notes\\\\notes\\\\{note}', 'w') as file:
            file.write(text)


# selects note and insert its text into the textbox
def select_value(current):
    global tb_state, secret_tb_state
    if switch.get() in (lang['gui']['avTabs'][0], lang['gui']['avTabs'][2]):
        global bas_current
        if bas_current == current:
            return
        bas_current = current
        if tb_state == 'disabled':
            tb.configure(state='normal')
            note_actions_opt.configure(state='normal')
            chapters_cmb.configure(state='normal')
            # rename_btn.configure(state='normal')
            # save_btn.configure(state='normal')
            # remind_btn.configure(state='normal')
            # make_it_secret_btn.configure(state='normal')
            # del_btn.configure(state='normal')
            tb_state = 'normal'
        if tb.get('0.0', 'end'):
            tb.delete('0.0', 'end')
        with open(f'{notebook_path}\\\\notes\\\\notes\\\\{current}', 'r', encoding='utf-8') as note:
            text = note.read()
            tb.insert('0.0', text)
        load_chapters(text)
        update_note_info('note', current)
    elif switch.get() == lang['gui']['avTabs'][1]:
        global secret_current
        if secret_current == current:
            return
        secret_current = current
        if secret_tb_state == 'disabled':
            secret_tb.configure(state='normal')
            # secret_rename_btn.configure(state='normal')
            # secret_save_btn.configure(state='normal')
            # secret_del_btn.configure(state='normal')
            secret_actions_opt.configure(state='normal')
            secret_tb_state = 'normal'
        if secret_tb:
            secret_tb.delete('0.0', 'end')
        with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{current}', 'rb') as s_n:
            secret_tb.insert('0.0', decrypt(s_n.read()))
        update_note_info('secret', current)


def get_chars_in_line(textbox, row):
    line_start_index = f"{row}.0"
    line_end_index = textbox.index(f"{row}.end")
    start_index_num = int(textbox.index(line_start_index).split('.')[1])
    end_index_num = int(textbox.index(line_end_index).split('.')[1])
    return end_index_num - start_index_num

def index_to_textbox_format(textbox, index):
    line_count = int(textbox.index('end-1c').split('.')[0])  # Получаем количество строк
    chars_in_lines = [get_chars_in_line(textbox, i + 1) for i in range(line_count)]
    
    total_chars = 0
    for row, chars_in_line in enumerate(chars_in_lines):
        if index < total_chars + chars_in_line:
            col = index - total_chars
            return f"{row + 1}.{col}"
        total_chars += chars_in_line
    return f"{line_count}.{index - total_chars}"  # Если индекс за пределами текста


def seek_to_chapter(val):
    tb_index = index_to_textbox_format(tb, av_chapters[val][0])
    tb.see(tb_index)
    # tb.mark_set("insert", tb_index)
    # tb.focus()


# changes page
def change_page(page):
    global current_page
    if page == lang['gui']['avTabs'][0]:
        current_page.pack_forget()
        fr_notes.pack(padx=10, fill='both', expand=True)
        current_page = fr_notes
        if tb.get('0.0', 'end'):
            app.after(100, tb.focus)
    elif page == lang['gui']['avTabs'][1]:
        current_page.pack_forget()
        if secrets_locked:
            fr_lockscreen.pack(padx=10, fill='both', expand=True)
            app.after(100, secrets_password_ent.focus_set)
            current_page = fr_lockscreen
        else:
            fr_secrets.pack(padx=10, fill='both', expand=True)
            current_page = fr_secrets
            if secret_tb.get('0.0', 'end'):
                app.after(100, secret_tb.focus)
    elif page == lang['gui']['avTabs'][2]:
        current_page.pack_forget()
        fr_settings.pack(padx=10, fill='both', expand=True)
        current_page = fr_settings


# show or hide password on lockscreen toggle function
def lockscreen_show():
    input_ = secrets_password_ent.get()
    if lcscreen_show.get():
        secrets_password_ent.delete(0, 'end')
        secrets_password_ent.configure(show='')
        secrets_password_ent.insert(0, input_)
    else:
        secrets_password_ent.delete(0, 'end')
        secrets_password_ent.configure(show='●')
        secrets_password_ent.insert(0, input_)


# password check correctness
def verify_user(event=None):
    if secrets_password_ent:
        pass_ = secrets_password_ent.get()
        if pass_ == secretsPass:
            secrets_password_ent.delete(0, 'end')
            unlock()
        else:
            mb.showerror(lang['mb']['err']['invPass'][0], lang['mb']['err']['invPass'][1])


# shows/unlocks secrets frame
def unlock():
    global secrets_locked, current_page
    fr_lockscreen.pack_forget()
    fr_secrets.pack(padx=10, fill='both', expand=True)
    current_page = fr_secrets
    secrets_locked = False
    if secret_tb.get('0.0', 'end'):
        app.after(100, secret_tb.focus)


# hides/locks secrets frame
def lock():
    global secrets_locked, current_page
    fr_secrets.pack_forget()
    fr_lockscreen.pack(padx=10, fill='both', expand=True)
    current_page = fr_lockscreen
    secrets_locked = True
    app.after(100, secrets_password_ent.focus)


# creates a new note
def create_note():
    def create(ev=None):
        global notes_names, secrets_names
        entered = name_ent.get()
        page = switch.get()
        if entered in (os.listdir(f'{notebook_path}\\\\notes\\\\notes') if page == lang['gui']['avTabs'][0] else
        os.listdir(f'{notebook_path}\\\\notes\\\\secrets')):
            mb.showerror(lang['mb']['err']['noteAlrExc'][0], lang['mb']['err']['noteAlrExc'][1])
            return
        if page == lang['gui']['avTabs'][0]:
            with open(f'{notebook_path}\\\\notes\\\\notes\\\\{entered}', 'w', encoding='utf-8') as note:
                note.write('')
            bas_notes.set(entered)
            notes_names = os.listdir(f'{notebook_path}\\\\notes\\\\notes')
            sorting('basic')
        elif page == lang['gui']['avTabs'][1]:
            with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{entered}', 'wb') as note:
                note.write(b'')
            time.sleep(0.1)

            secret_notes.set(entered)
            secrets_names = os.listdir(f'{notebook_path}\\\\notes\\\\secrets')
            sorting('secret')

        add_window.destroy()
        select_value(entered)
        mb.showinfo(lang['mb']['inf']['noteCrtd'][0], f"{lang['mb']['inf']['noteCrtd'][1][0]} {entered} {lang['mb']['inf']['noteCrtd'][1][1]}")

    def validate_note_name(text, action):
        return action == '0' or (len(text) < 23 and not any((symbol in r'\\\\/:*?"<>|') for symbol in text))

    add_window = ctk.CTkToplevel()
    add_window.title(lang['dia']['noteAdd']['title'])
    add_window.resizable(False, False)
    add_window.grab_set()

    ctk.CTkLabel(master=add_window, text=lang['dia']['noteAdd']['l'], font=('Arial', font_size_label)).pack(pady=15)
    name_ent = ctk.CTkEntry(master=add_window, font=('Arial', font_size_optionMenu + 1), width=x(40))
    name_ent.configure(validate='key', validatecommand=(name_ent.register(validate_note_name), '%P', '%d'))
    name_ent.bind('<Return>', create)
    name_ent.pack(padx=20, fill='x')
    add_name = ctk.CTkButton(master=add_window, text=lang['dia']['noteAdd']['b'], font=('Arial', font_size_button), width=0,
                             command=create)
    add_name.pack(pady=20, ipadx=10)

    add_window.after(100, name_ent.focus_set)


def note_action(val):
    if switch.get() == lang['gui']['avTabs'][0]:
        note_actions_opt.set(lang['gui']['actBtn'])
    elif switch.get() == lang['gui']['avTabs'][1]:
        secret_actions_opt.set(lang['gui']['actBtn'])
    if val == lang['gui']['not']['actList'][0]:
            rename_note()
    elif val == lang['gui']['not']['actList'][1]:
            save()
    elif val == lang['gui']['not']['actList'][2]:
            delete()
    elif val == lang['gui']['not']['actList'][3]:
            remind_win()
    elif val == lang['gui']['not']['actList'][4]:
            make_it_secret()
    elif val == lang['gui']['sec']['sec']['actList'][3]:
            lock()


def rename_note():
    def rename(new):
        rename_window.destroy()
        if current_page == fr_notes:
            os.rename(f'{notebook_path}\\\\notes\\\\notes\\\\{old_name}',
                      f'{notebook_path}\\\\notes\\\\notes\\\\{new}')
            mb.showinfo(lang['mb']['inf']['rnameNo'][0], f"{lang['mb']['inf']['rnameNo'][1][0]} {old_name} {lang['mb']['inf']['rnameNo'][1][1]} {new}!")
            notes_names.remove(old_name)
            notes_names.append(new)
            sorting('basic')
            bas_notes.configure(values=notes_names)
            bas_notes.set(new)

        elif current_page == fr_secrets:
            os.rename(f'{notebook_path}\\\\notes\\\\secrets\\\\{old_name}',
                      f'{notebook_path}\\\\notes\\\\secrets\\\\{new}')
            mb.showinfo(lang['mb']['inf']['rnameNo'][0], f"{lang['mb']['inf']['rnameSe'][1][0]} {old_name} {lang['mb']['inf']['rnameSe'][1][1]} {new}!")
            secrets_names.remove(old_name)
            secrets_names.append(new)
            sorting('secret')
            secret_notes.configure(values=secrets_names)
            secret_notes.set(new)

    def validate_note_name(text, action):
        return action == '0' or (len(text) < 23 and not any((symbol in r'\\\\/:*?"<>|') for symbol in text))

    rename_window = ctk.CTkToplevel()
    rename_window.title(lang['dia']['rname']['title'])
    rename_window.resizable(False, False)
    rename_window.grab_set()

    old_name = bas_current if current_page == fr_notes else secret_name.get()

    ctk.CTkLabel(master=rename_window, text=lang['dia']['rname']['l'],
                 font=('Arial', font_size_label)).pack(padx=20, pady=20)
    new_name = ctk.CTkEntry(master=rename_window, font=('Arial', font_size_optionMenu + 1), width=x(40))
    new_name.configure(validate='key', validatecommand=(new_name.register(validate_note_name), '%P', '%d'))
    new_name.insert('0', old_name)
    new_name.bind('<Return>', lambda e: rename(new_name.get()))
    new_name.pack(padx=20)
    confirm_btn = ctk.CTkButton(master=rename_window, text=lang['dia']['rname']['b'], font=('Arial', font_size_button),
                                width=0, command=lambda: rename(new_name.get()))
    confirm_btn.pack(pady=20, ipadx=10)

    rename_window.after(100, new_name.focus_set)


# deletes chosen note
def delete():
    global tb_state, secret_tb_state
    if switch.get() == lang['gui']['avTabs'][0]:
        chosen = bas_notes.get()
        if mb.askyesno(lang['mb']['que']['delConf'][0], f"{lang['mb']['que']['delConf'][1]} {chosen}?"):
            notes_names.remove(chosen)
            os.remove(f'{notebook_path}\\\\notes\\\\notes\\\\{chosen}')
            tb.delete('0.0', 'end')
            tb.configure(state='disabled')
            # rename_btn.configure(state='disabled')
            # save_btn.configure(state='disabled')
            # del_btn.configure(state='disabled')
            # remind_btn.configure(state='disabled')
            # make_it_secret_btn.configure(state='disabled')
            note_actions_opt.configure(state='disabled')
            l1.pack_forget()
            chapters_cmb.pack_forget()
            tb_state = 'disabled'
            bas_notes.configure(values=notes_names)
            bas_notes.set(lang['gui']['nChsn'])
            date.configure(text='')
            size_lbl.configure(text='')
    elif switch.get() == lang['gui']['avTabs'][1]:
        chosen = secret_notes.get()
        if mb.askyesno(lang['mb']['que']['delConf'][0], f"{lang['mb']['que']['delConf'][1]} {chosen}?"):
            secrets_names.remove(chosen)
            os.remove(f'{notebook_path}\\\\notes\\\\secrets\\\\{chosen}')
            secret_tb.delete('0.0', 'end')
            secret_tb.configure(state='disabled')
            # secret_rename_btn.configure(state='disabled')
            # secret_save_btn.configure(state='disabled')
            # secret_del_btn.configure(state='disabled')
            secret_actions_opt.configure(state='disabled')
            secret_tb_state = 'disabled'
            secret_notes.configure(values=secrets_names)
            secret_notes.set(lang['gui']['nChsn'])
            secret_date.configure(text='')


# changes secrets password
def change_password():
    def current_show():
        input_ = cur_pass.get()
        if cur_show.get():
            cur_pass.delete(0, 'end')
            cur_pass.configure(show='')
            cur_pass.insert(0, input_)
        else:
            cur_pass.delete(0, 'end')
            cur_pass.configure(show='●')
            cur_pass.insert(0, input_)

    def new_show_():
        input_ = new_pass.get()
        if new_show.get():
            new_pass.delete(0, 'end')
            new_pass.configure(show='')
            new_pass.insert(0, input_)
        else:
            new_pass.delete(0, 'end')
            new_pass.configure(show='●')
            new_pass.insert(0, input_)

    def change(event=None):
        global secretsPass
        current = cur_pass.get()
        new = new_pass.get()
        if current:
            if current == secretsPass:
                pass
            elif current == new:
                mb.showerror(lang['mb']['err']['simmPass'][0], lang['mb']['err']['simmPass'][1])
                return
            else:
                mb.showerror(lang['mb']['err']['invPriPass'], lang['mb']['err']['invPriPass'][1])
                return
        else:
            mb.showerror(lang['mb']['err']['noCurrPass'][0], lang['mb']['err']['noCurrPass'][1])
            return
        if new:
            if len(new) < 4:
                mb.showerror(lang['mb']['err']['shortPass'][0], lang['mb']['err']['shortPass'][1])
                return
            secretsPass = new

            change_window.destroy()
            os.system(f'attrib -h {notebook_path}\\\\conf\\\\pd')
            with open(f'{notebook_path}\\\\conf\\\\pd', 'wb') as file:
                file.write(encrypt(secretsPass))
            os.system(f'attrib +h {notebook_path}\\\\conf\\\\pd')
            mb.showinfo(lang['mb']['inf']['passChd'][0], lang['mb']['inf']['passChd'][1])
        else:
            mb.showerror(lang['mb']['err']['noNewPass'][0], lang['mb']['err']['noNewPass'][1])

    change_window = ctk.CTkToplevel()
    change_window.title(lang['dia']['passCh']['title'])
    change_window.resizable(False, False)
    change_window.grab_set()

    bg = change_window.cget('bg')

    ctk.CTkLabel(master=change_window, text=lang['dia']['passCh']['l1'],
                 font=('Arial', font_size_label)).pack(padx=15, pady=15, anchor='w')
    cur_pass_row = Frame(master=change_window, bg=bg)
    cur_pass_row.pack(padx=10, fill='x')
    cur_pass = ctk.CTkEntry(master=cur_pass_row, width=x(40), font=('Arial', font_size_optionMenu + 1), show='●')
    cur_pass.pack(side='left', fill='x', expand=True, padx=5)
    cur_show = ctk.CTkCheckBox(master=cur_pass_row, text='👁️', font=('Segoe UI Emoji', font_size_label), onvalue=True,
                               offvalue=False, width=0, command=current_show)
    cur_show.pack(side='right', padx=5)

    ctk.CTkLabel(master=change_window, text=lang['dia']['passCh']['l2'],
                 font=('Arial', font_size_label)).pack(padx=15, pady=15, anchor='w')
    new_pass_row = Frame(master=change_window, bg=bg)
    new_pass_row.pack(padx=10, fill='x')
    new_pass = ctk.CTkEntry(master=new_pass_row, width=x(40), font=('Arial', font_size_optionMenu + 1), show='●')
    new_pass.bind('<Return>', change)
    new_pass.pack(side='left', fill='x', expand=True, padx=5)
    new_show = ctk.CTkCheckBox(master=new_pass_row, text='👁️', font=('Segoe UI Emoji', font_size_label), onvalue=True,
                               offvalue=False, width=0, command=new_show_)
    new_show.pack(side='right', padx=5)
    conf = ctk.CTkButton(master=change_window, text=lang['dia']['passCh']['b'], font=('Arial', font_size_button),
                         command=change)
    conf.pack(pady=20, ipadx=10)

    change_window.mainloop()


# sorts the notes
def sorting(notes_type):
    if notes_type == 'both':
        sorting('basic')
        sorting('secret')
        return
    match settings['sorting']:
        case 'a-z':
            if notes_type == 'basic':
                notes_names.sort()
            elif notes_type == 'secret':
                secrets_names.sort()
        case 'z-a':
            if notes_type == 'basic':
                notes_names.sort(reverse=True)
            elif notes_type == 'secret':
                secrets_names.sort(reverse=True)
        case _:
            if notes_type == 'basic':
                notes_names.sort(
                    key=lambda x: (time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{x}'))[0],
                                   time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{x}'))[1],
                                   time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{x}'))[2],
                                   time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{x}'))[3],
                                   time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{x}'))[4]),
                    reverse=True if settings['sorting'] == 'newFirst' else False)
            elif notes_type == 'secret':
                secrets_names.sort(
                    key=lambda x: (
                        time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{x}'))[0],
                        time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{x}'))[1],
                        time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{x}'))[2],
                        time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{x}'))[3],
                        time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{x}'))[4]),
                    reverse=True if settings['sorting'] == 'newFirst' else False)
    if notes_type == 'basic':
        bas_notes.configure(values=notes_names)
    else:
        secret_notes.configure(values=secrets_names)


# shows some information before restart the app
def success(setting, val):
    mb.showinfo(lang['mb']['inf']['settChd'][0], f"{lang['mb']['inf']['settChd'][1][0]} {setting} {lang['mb']['inf']['settChd'][1][1]} {val} {lang['mb']['inf']['settChd'][1][2]}")
    # write_data()
    confirm()
    Popen(['pythonw', 'main.py'], creationflags=DETACHED_PROCESS)
    exit(0)


def set_sorting(val):
    if val == lang['gui']['set'][1][1][0]:
        if settings['sorting'] == 'a-z':
            return
        settings['sorting'] = 'a-z'
    elif val == lang['gui']['set'][1][1][1]:
        if settings['sorting'] == 'z-a':
            return
        settings['sorting'] = 'z-a'
    elif val == lang['gui']['set'][1][1][2]:
        if settings['sorting'] == 'newFirst':
            return
        settings['sorting'] = 'newFirst'
    elif val == lang['gui']['set'][1][1][3]:
        if settings['sorting'] == 'oldFirst':
            return
        settings['sorting'] = 'oldFirst'
    sorting('both')


def set_font_size(val):
    if val == lang['gui']['set'][2][1][0]:
        if settings['fontSize']['str'] == 'small':
            return
        settings['fontSize'] = {'str': 'small', 'label': 16, 'button': 14, 'optionMenu': 13}
        # success(lang['gui']['props'][0], val)
    elif val == lang['gui']['set'][2][1][1]:
        if settings['fontSize']['str'] == 'medium':
            return
        settings['fontSize'] = {'str': 'medium', 'label': 18, 'button': 16, 'optionMenu': 15}
        # success(lang['gui']['props'][0], val)
    elif val == lang['gui']['set'][2][1][2]:
        if settings['fontSize']['str'] == 'large':
            return
        settings['fontSize'] = {'str': 'large', 'label': 21, 'button': 19, 'optionMenu': 18}
    success(lang['gui']['props'][0], val)


def set_theme(val):
    def change_bg():
        bg = '#2B2B2B' if ctk.AppearanceModeTracker.appearance_mode == 1 else '#DBDBDB'
        panel_notes_top.configure(bg=bg)
        panel_notes_bottom.configure(bg=bg)
        group_lockscreen.configure(bg=bg)
        pass_entry_row.configure(bg=bg)
        panel_secrets_top.configure(bg=bg)
        panel_secrets_bottom.configure(bg=bg)

    if val == lang['gui']['set'][3][1][0]:
        if settings['appearanceMode'] == 'Light':
            return
        settings['appearanceMode'] = 'Light'
        ctk.set_appearance_mode('Light')
        panel_notes_top.configure(bg='#DBDBDB')
        panel_notes_bottom.configure(bg='#DBDBDB')
        group_lockscreen.configure(bg='#DBDBDB')
        pass_entry_row.configure(bg='#DBDBDB')
        panel_secrets_top.configure(bg='#DBDBDB')
        panel_secrets_bottom.configure(bg='#DBDBDB')
    elif val == lang['gui']['set'][3][1][1]:
        if settings['appearanceMode'] == 'Dark':
            return
        settings['appearanceMode'] = 'Dark'
        ctk.set_appearance_mode('Dark')
        panel_notes_top.configure(bg='#2B2B2B')
        panel_notes_bottom.configure(bg='#2B2B2B')
        group_lockscreen.configure(bg='#2B2B2B')
        pass_entry_row.configure(bg='#2B2B2B')
        panel_secrets_top.configure(bg='#2B2B2B')
        panel_secrets_bottom.configure(bg='#2B2B2B')
    elif val == lang['gui']['set'][3][1][2]:
        if settings['appearanceMode'] == 'System':
            return
        settings['appearanceMode'] = 'System'
        ctk.set_appearance_mode('System')
        app.after(300, change_bg)


def set_color_theme(val):
    if val == lang['gui']['set'][4][1][0]:
        if settings['colorTheme'] == 'blue':
            return
        settings['colorTheme'] = 'blue'
        # success(lang['gui']['props'][1], val)
    elif val == lang['gui']['set'][4][1][1]:
        if settings['colorTheme'] == 'green':
            return
        settings['colorTheme'] = 'green'
        # success(lang['gui']['props'][1], val)
    elif val == lang['gui']['set'][4][1][2]:
        if settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\red.json':
            return
        settings['colorTheme'] = f'{notebook_path}\\\\custom_colors\\\\red.json'
        # success(lang['gui']['props'][1], val)
    elif val == lang['gui']['set'][4][1][3]:
        if settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\yelow.json':
            return
        settings['colorTheme'] = f'{notebook_path}\\\\custom_colors\\\\yellow.json'
        # success(lang['gui']['props'][1], val)
    elif val == lang['gui']['set'][4][1][4]:
        if settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\purple.json':
            return
        settings['colorTheme'] = f'{notebook_path}\\\\custom_colors\\\\purple.json'
    success(lang['gui']['props'][1], val)


def set_start():
    if start_sw.get():
        if settings['startLast']:
            return
        settings['startLast'] = True
        start_sw.configure(text=lang['gui']['y'])
    else:
        if not settings['startLast']:
            return
        settings['startLast'] = False
        settings['lastNote'] = None
        start_sw.configure(text=lang['gui']['n'])


def set_topmost():
    if topmost_sw.get():
        if settings['isTopmost']:
            return
        settings['isTopmost'] = True
        topmost_sw.configure(text=lang['gui']['y'])
        Thread(target=app_state_check, daemon=True).start()
    else:
        if not settings['isTopmost']:
            return
        settings['isTopmost'] = False
        topmost_sw.configure(text=lang['gui']['n'])
    app.attributes('-topmost', settings['isTopmost'])


def set_show_size():
    if show_size_sw.get():
        if settings['showSize']:
            return
        settings['showSize'] = True
        show_size_sw.configure(text=lang['gui']['y'])
        size_lbl.pack(side='left')
        if note_actions_opt.cget('state') != 'disabled':
            file_size = os.path.getsize(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}')
            if file_size // 1_000_000 >= 1:
                size_lbl.configure(text=str(round(file_size / 1_000_000, 1)) + ' ' + lang['gui']['not']['sizeLett'][2])
            elif file_size // 1_000 >= 1:
                size_lbl.configure(text=str(round(file_size / 1_000, 1)) + ' ' + lang['gui']['not']['sizeLett'][1])
            else:
                size_lbl.configure(text=str(round(file_size, 1)) + ' ' + lang['gui']['not']['sizeLett'][0])
    else:
        if not settings['showSize']:
            return
        settings['showSize'] = False
        show_size_sw.configure(text=lang['gui']['n'])
        size_lbl.pack_forget()


def set_chapter_pattern(val):
    if val[0] != settings['chapterPattern']:
        if mb.askyesno('Подтверждение', 'Вы только что изменили шаблон поиска разделов, хотите ли Вы также автоматически изменить вид разделов во всех ваших заметках? Если нет, то разделы не будут отображатся до тех пор пока вы не измените их вид ВРУЧНУЮ в соответствии с выбраным шаблоном.'):
            refactor_chapters((val[0], val[-1]))
            global bas_current
            if bas_current != lang['gui']['nChsn']:
                bas_current = None
                select_value(name.get())
            mb.showinfo('Успех', 'Вид разделов в ваших заметках успешно изменён на новый.')
        settings['chapterPattern'] = val[0]
        write_data()
    else:
        return


def set_lang(val):
    # global lang
    if val == lang['gui']['set'][9][1][0]:
        if settings['lang'] == 'en':
            return
        settings['lang'] = 'en'
    elif val == lang['gui']['set'][9][1][1]:
        if settings['lang'] == 'ru':
            return
        settings['lang'] = 'ru'
    elif val == lang['gui']['set'][9][1][2]:
        if settings['lang'] == 'pl':
            return
        settings['lang'] = 'pl'
    success(lang['gui']['props'][2], val)
            

# saves name of the last chosen note before closing the app
def check_start():
    if settings['startLast']:
        bas_notes.set(settings['lastNote'])
        select_value(settings['lastNote'])


# reminder thread function
def reminder(rem_time, n_n, n_t, is_delete):
    global notes_names
    while rem_time != time.strftime('%H:%M', time.localtime()):
        time.sleep(1)
    else:
        mb.showinfo(n_n, n_t)
        if is_delete:
            os.remove(f'{notebook_path}\\\\notes\\\\notes\\\\{n_n}')
        try:
            if n_n == bas_notes.get():
                bas_notes.set(lang['gui']['nChsn'])
                date.configure(text='')
                if settings['showSize']:
                    size_lbl.configure(text='')
                tb.delete('0.0', 'end')
                tb.configure(state='disabled')
                note_actions_opt.configure(state='disabled')
                l1.pack_forget()
                chapters_cmb.pack_forget()
                # del_btn.configure(state='disabled')
                # save_btn.configure(state='disabled')
                # remind_btn.configure(state='disabled')
                # make_it_secret_btn.configure(state='disabled')
            notes_names = os.listdir(f'{notebook_path}\\\\notes\\\\notes')
            bas_notes.configure(values=notes_names)
        except RuntimeError:
            pass


# adds time for reminding about chosen note
def remind_win():
    def remind(ev=None):
        user_input = rem_ent.get()
        if not user_input:
            return
        if re.match('^[0-9]{2}:[0-9]{2}$', user_input):
            time_ = [user_input, time.strftime('%H:%M', time.localtime())]
            time_.sort(key=lambda x: (x.split(':')[0], x.split(':')[1]))
            if user_input == time_[0]:
                mb.showerror(lang['mb']['err']['invTmForRem'][0],
                             f"{lang['mb']['err']['invTmForRem'][1][0]} {user_input}{lang['mb']['err']['invTmForRem'][1][1]}")
                return
            remind_window.destroy()
            save()
            with open(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}', 'r', encoding='utf-8') as n_t:
                text = n_t.read()
            is_delete = del_aft_rem.get()
            Thread(target=reminder, args=(user_input, bas_current, text, is_delete), daemon=False,
                   name='reminder').start()
            mb.showinfo(lang['mb']['inf']['remCre'][0], f"{lang['mb']['err']['remCre'][1][0]} {bas_current} {lang['mb']['err']['remCre'][1][1]} {user_input}!")

        else:
            mb.showerror(lang['mb']['err']['invTime'][0], f"{user_input} {lang['mb']['err']['invTime'][1]}")

    def validate_remind_time(text, action):
        return action == '0' or (len(text) < 6 and all((symbol in '0123456789:') for symbol in text))

    remind_window = ctk.CTkToplevel()
    remind_window.title(lang['dia']['remSett']['title'])
    remind_window.resizable(False, False)
    remind_window.grab_set()

    ctk.CTkLabel(master=remind_window, text=lang['dia']['remSett']['l'],
                 font=('Arial', font_size_label)).pack(padx=20, pady=20)
    rem_ent = ctk.CTkEntry(master=remind_window, font=('Arial', font_size_optionMenu + 1), width=0, justify='center')
    rem_ent.configure(validate='key', validatecommand=(rem_ent.register(validate_remind_time), '%P', '%d'))
    rem_ent.bind('<Return>', remind)
    rem_ent.pack(padx=50, fill='x')
    del_aft_rem = ctk.CTkCheckBox(master=remind_window, text=lang['dia']['remSett']['ch'],
                                  font=('Arial', font_size_label),
                                  onvalue=True, offvalue=False)
    del_aft_rem.pack(padx=20, pady=20)
    rem_btn = ctk.CTkButton(master=remind_window, text=lang['dia']['remSett']['b'], font=('Arial', font_size_button), width=0,
                            command=remind)
    rem_btn.pack(pady=10, ipadx=10)

    remind_window.after(100, rem_ent.focus_set)


def make_it_secret():
    chosen = bas_current
    if mb.askyesno(lang['mb']['que']['mkItSecr'][0], f"{lang['mb']['que']['mkItSecr'][1]} {chosen}?"):
        text = tb.get('0.0', 'end')[:-1]
        os.rename(f'{notebook_path}\\\\notes\\\\notes\\\\{chosen}', f'{notebook_path}\\\\notes\\\\secrets\\\\{chosen}')
        with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{chosen}', 'wb') as secret:
            secret.write(encrypt(text))

        notes_names.remove(chosen)
        bas_notes.configure(values=notes_names)
        bas_notes.set(lang['gui']['nChsn'])
        tb.delete('0.0', 'end')
        tb.configure(state='disabled')
        # make_it_secret_btn.configure(state='disabled')
        # remind_btn.configure(state='disabled')
        # del_btn.configure(state='disabled')
        # save_btn.configure(state='disabled')
        # rename_btn.configure(state='disabled')
        note_actions_opt.configure(state='disabled')
        l1.pack_forget()
        chapters_cmb.pack_forget()
        date.configure(text='')
        if settings['showSize']:
            size_lbl.configure(text='')
        if settings['startLast']:
            settings['lastNote'] = None
            write_data()
        secrets_names.append(chosen)
        sorting('secret')
        mb.showinfo(lang['mb']['que']['mdeItSecrSucc'][0], f"{lang['mb']['que']['mdeItSecrSucc'][1][0]} {chosen} {lang['mb']['que']['mdeItSecrSucc'][1][1]}")


# saves last chosen note's text before closing the app
def last_save(note_type):
    match note_type:
        case 'basic':
            with open(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}', 'w', encoding='utf-8') as note:
                note.write(tb.get('0.0', 'end')[:-1])
        case 'secret':
            secret_choosed_text = encrypt(secret_tb.get('0.0', 'end')[:-1])
            with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{secret_name.get()}', 'wb') as secret:
                secret.write(secret_choosed_text)


# asks to save or don't to save changes in the last chosen note's text
def confirm():
    if switch.get() in (lang['gui']['avTabs'][0], lang['gui']['avTabs'][2]):
        if note_actions_opt.cget('state') == 'normal':
            note_name = bas_current
            with open(f'{notebook_path}\\\\notes\\\\notes\\\\{note_name}', 'r', encoding='utf-8') as note:
                note_text = note.read()
            if note_text != tb.get('0.0', 'end')[:-1]:
                answ = mb.askyesnocancel(lang['mb']['que']['saveNClseConf'][0], f"{lang['mb']['que']['saveNClseConf'][1][0]} {note_name} {lang['mb']['que']['saveNClseConf'][1][1]}")
                if answ:
                    last_save('basic')
                elif answ is None:
                    return
        if settings['startLast']:
            if bas_current != lang['gui']['nChsn']:
                settings['lastNote'] = bas_current
    elif switch.get() == lang['gui']['avTabs'][1]:
        if secret_actions_opt.cget('state') == 'normal':
            note_name = secret_name.get()
            with open(f'{notebook_path}\\\\notes\\\\secrets\\\\{note_name}', 'rb') as note:
                note_text = decrypt(note.read())
            if note_text != secret_tb.get('0.0', 'end')[:-1]:
                answ = mb.askyesnocancel(lang['mb']['que']['saveNClseConf'][0], f"{lang['mb']['que']['saveNClseConf'][1][0]} {note_name} {lang['mb']['que']['saveNClseConf'][1][1]}")
                if answ:
                    last_save('secret')
                elif answ is None:
                    return
    settings['appGeometry'] = app.wm_geometry() if app.state() == 'normal' else 'zoomed'
    write_data()
    app.destroy()


# checks keyboard layout
def ckl():
    u = ctypes.windll.LoadLibrary("user32.dll")
    pf = getattr(u, "GetKeyboardLayout")
    print(hex(pf(0)))
    if hex(pf(0)) in ['0x4190419', '-0xf57fbde']:
        return True
    else:
        return False


# makes able to use some custom hotkeys
def commands(ev):
    if ev.char == '':  # Ctrl+W
        confirm()
    elif ev.char == '':  # Ctrl+N
        if switch.get() == lang['gui']['avTabs'][0] or (switch.get() == lang['gui']['avTabs'][1] and fr_lockscreen.place_info()):
            create_note()
    elif ev.char == '':  # Ctrl+R
        if switch.get() == lang['gui']['avTabs'][0] and note_actions_opt.cget('state') == 'normal':
            remind_win()
    elif ev.char == '':  # Ctrl+L
        if switch.get() == lang['gui']['avTabs'][1]:
            lock()
    elif (ev.state == 393216 or ev.state == 393220) and ev.keysym == 'Left':  # Alt + arrow_left
        if current_page == fr_notes:
            switch.set(lang['gui']['avTabs'][2])
            change_page(lang['gui']['avTabs'][2])
        elif current_page == fr_secrets or current_page == fr_lockscreen:
            switch.set(lang['gui']['avTabs'][0])
            change_page(lang['gui']['avTabs'][0])
        elif current_page == fr_settings:
            switch.set(lang['gui']['avTabs'][1])
            change_page(lang['gui']['avTabs'][1])
    elif (ev.state == 393216 or ev.state == 393220) and ev.keysym == 'Right':  # Alt + arrow_right
        if current_page == fr_notes:
            switch.set(lang['gui']['avTabs'][1])
            change_page(lang['gui']['avTabs'][1])
        elif current_page == fr_secrets or current_page == fr_lockscreen:
            switch.set(lang['gui']['avTabs'][2])
            change_page(lang['gui']['avTabs'][2])
        elif current_page == fr_settings:
            switch.set(lang['gui']['avTabs'][0])
            change_page(lang['gui']['avTabs'][0])
    else:
        if (str(app.focus_get())[:-6] == str(tb)) or (str(app.focus_get())[:-6] == str(secret_tb)):
            text_commands(ev)


# makes able to use some text hotkeys on Russian or Ukrainian keyboard layouts
def text_commands(ev):
    if ev.char == '':  # Ctrl+S
        save()
    elif ev.char == '':  # Ctrl+C
        if ckl():
            pyperclip.copy((tb if switch.get() == lang['gui']['avTabs'][1] else secret_tb).selection_get())
    elif ev.char == '':  # Ctrl+V
        if ckl():
            data = pyperclip.paste()
            textbox = (tb if switch.get() == lang['gui']['avTabs'][1] else secret_tb)
            try:
                sel = textbox.selection_get()
                print(f'selection "{sel}"')
                textbox.delete(textbox.index('sel.first'), textbox.index('sel.last'))
            except TclError:
                pass
            textbox.insert(textbox.index('insert'), data)
    elif ev.char == '':  # Ctrl+X
        if ckl():
            textbox = (tb if switch.get() == lang['gui']['avTabs'][1] else secret_tb)
            try:
                sel = textbox.selection_get()
                pyperclip.copy(sel)
                textbox.delete(textbox.index('sel.first'), textbox.index('sel.last'))
            except TclError:
                pass


def changed_crated_toggle(ev=None):
    global date_state, secret_date_state
    if current_page == fr_notes:

        if date_state == 'changed':
            created_time = time.localtime(os.path.getctime(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}'))
            date.configure(text=lang['gui']['tCh'][1] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", created_time))
            date_state = 'created'

        elif date_state == 'created':
            changed_time = time.localtime(os.path.getmtime(f'{notebook_path}\\\\notes\\\\notes\\\\{bas_current}'))
            date.configure(text=lang['gui']['tCh'][0] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", changed_time))
            date_state = 'changed'

    elif current_page == fr_secrets:

        if secret_date_state == 'changed':
            created_time = time.localtime(
                os.path.getctime(f'{notebook_path}\\\\notes\\\\secrets\\\\{secret_name.get()}'))
            secret_date.configure(text=lang['gui']['tCh'][1] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", created_time))
            secret_date_state = 'created'

        elif secret_date_state == 'created':
            changed_time = time.localtime(
                os.path.getmtime(f'{notebook_path}\\\\notes\\\\secrets\\\\{secret_name.get()}'))
            secret_date.configure(text=lang['gui']['tCh'][0] + '    ' + time.strftime(f"%d.%m.%Y  {lang['gui']['tCh'][2]}  %H:%M", changed_time))
            secret_date_state = 'changed'


def x(percents: int | float) -> int:
    """Returns length in px that takes passed number of percents of app width"""
    return int(app_width * percents / 100)


def y(percents: int | float) -> int:
    """Returns length in px that takes passed number of percents of app height"""
    return int(app_height * percents / 100)


def grey_to_hex(grey):
    """Converts greyXX color to hex"""
    if ctk.get_appearance_mode() == 'Light':
        grey = grey[0]
    else:
        grey = grey[1]
    return "#" + hex(ceil(int(grey[4:]) * 2.55))[2:] * 3


def app_state_check():
    def check():
        global app_state
        if app.wm_state() == 'zoomed' and app_state == 'normal':
            app.attributes('-topmost', False)
            app_state = 'zoomed'
        elif app.wm_state() == 'normal' and app_state == 'zoomed':
            app.attributes('-topmost', True)
            app_state = 'normal'

    while settings['isTopmost']:
        check()
        time.sleep(1)


# creating app required directories or files if they don't exist
# if not (os.path.exists(notebook_path) and os.path.isdir(notebook_path)):
#     os.mkdir(notebook_path)

# if not (os.path.exists(f'{notebook_path}\\\\notes') and os.path.isdir(f'{notebook_path}\\\\notes')):
#     os.mkdir(f'{notebook_path}\\\\notes')

# if not (os.path.exists(f'{notebook_path}\\\\notes\\\\notes') and os.path.isdir(f'{notebook_path}\\\\notes\\\\notes')):
#     os.mkdir(f'{notebook_path}\\\\notes\\\\notes')

# if not (os.path.exists(f'{notebook_path}\\\\notes\\\\secrets') and os.path.isdir(f'{notebook_path}\\\\notes\\\\secrets')):
#     os.mkdir(f'{notebook_path}\\\\notes\\\\secrets')

if not os.path.exists(f'{notebook_path}\\\\conf\\\\settings.json'):
    from variables import DEFAULT_SETTINGS
    with open(f'{notebook_path}\\\\conf\\\\settings.json', 'w') as njs:
        njs.write(DEFAULT_SETTINGS)
    del njs
with open(f'{notebook_path}\\\\conf\\\\settings.json', 'r', encoding='utf-8') as notes:
    settings = json.loads(notes.read())

if not os.path.exists(f"{notebook_path}\\\\conf\\\\lang\\\\{settings['lang']}.json"):
    match settings['lang']:
        case 'ru':
            from variables import LANG_RU
            with open(f'{notebook_path}\\\\conf\\\\lang\\\\ru.json', 'w') as ru:
                ru.write(LANG_RU)
        case 'en':
            from variables import LANG_EN
            with open(f'{notebook_path}\\\\conf\\\\lang\\\\en.json', 'w') as en:
                en.write(LANG_EN)
with open(f"{notebook_path}\\\\conf\\\\lang\\\\{settings['lang']}.json", 'r') as file:
    lang: dict = json.loads(file.read())
    
# if not os.path.exists(f'{notebook_path}\\\\conf\\\\pd'):
#     with open(f'{notebook_path}\\\\conf\\\\pd', 'w'):
#         pass
#     os.system(f'attrib +h "{notebook_path}\\\\conf\\\\pd"')

# if not (os.path.exists(f'{notebook_path}\\\\custom_colors') and
#         os.path.isdir(f'{notebook_path}\\\\custom_colors')):
#     os.mkdir(f'{notebook_path}\\\\custom_colors')

# if not os.path.exists(f'{notebook_path}\\\\custom_colors\\\\red.json'):
#     try:
#         from variables import RED
#         with open(f'{notebook_path}\\\\custom_colors\\\\red.json', 'w') as red_theme:
#             red_theme.write(RED)
#         del red_theme
#     except ModuleNotFoundError:
#         mb.showerror('Ошибка', 'Не найден файл приложения "variables.py".\\\\n'
#                                'Переустановите папку с приложением или свяжитесь с разработчиком.')
#         raise SystemExit
#     except ImportError as error:
#         mb.showerror('Ошибка', 'Ошибка импорта. Переустановите папку с приложением или свяжитесь с разработчиком.')
#         with open(f'{notebook_path}\\\\conf\\\\debug.log', 'a') as log:
#             log.write(f'{time.strftime("[ %d.%m.%Y | %H:%M:%S ]", time.localtime())}: Raised ImportError: {error.msg}')
#         raise SystemExit


# if not os.path.exists(f'{notebook_path}\\\\custom_colors\\\\yellow.json'):
#     try:
#         from variables import YELLOW
#         with open(f'{notebook_path}\\\\custom_colors\\\\yellow.json', 'w') as yellow_theme:
#             yellow_theme.write(YELLOW)
#         del yellow_theme
#     except ModuleNotFoundError:
#         mb.showerror('Ошибка', 'Не найден файл приложения "variables.py".\\\\n'
#                                'Переустановите папку с приложением или свяжитесь с разработчиком.')
#         raise SystemExit
#     except ImportError as error:
#         mb.showerror('Ошибка', 'Ошибка импорта. Переустановите папку с приложением или свяжитесь с разработчиком.')
#         with open(f'{notebook_path}\\\\conf\\\\debug.log', 'a') as log:
#             log.write(f'{time.strftime("[ %d.%m.%Y | %H:%M:%S ]", time.localtime())}: Raised ImportError: {error.msg}')
#         raise SystemExit


# if not os.path.exists(f'{notebook_path}\\\\custom_colors\\\\purple.json'):
#     try:
#         from variables import PURPLE
#         with open(f'{notebook_path}\\\\custom_colors\\\\purple.json', 'w') as purple_theme:
#             purple_theme.write(PURPLE)
#         del purple_theme
#     except ModuleNotFoundError:
#         mb.showerror('Ошибка', 'Не найден файл приложения "variables.py".\\\\n'
#                                'Переустановите папку с приложением или свяжитесь с разработчиком.')
#         raise SystemExit
#     except ImportError as error:
#         mb.showerror('Ошибка', 'Ошибка импорта. Переустановите папку с приложением или свяжитесь с разработчиком.')
#         with open(f'{notebook_path}\\\\conf\\\\debug.log', 'a') as log:
#             log.write(f'{time.strftime("[ %d.%m.%Y | %H:%M:%S ]", time.localtime())}: Raised ImportError: {error.msg}')
#         raise SystemExit


# if not os.path.exists(f'{notebook_path}\\\\conf\\\\nb.ico'):
#     try:
#         from variables import ICON
#         with open(f'{notebook_path}\\\\conf\\\\nb.ico', 'wb') as icon:
#             red_theme.write(ICON)
#         del icon
#     except ModuleNotFoundError:
#         mb.showerror('Ошибка', 'Не найден файл приложения "variables.py".\\\\n'
#                                'Переустановите папку с приложением или свяжитесь с разработчиком.')
#         raise SystemExit
#     except ImportError as error:
#         mb.showerror('Ошибка', 'Ошибка импорта. Переустановите папку с приложением или свяжитесь с разработчиком.')
#         with open(f'{notebook_path}\\\\conf\\\\debug.log', 'a') as log:
#             log.write(f'{time.strftime("[ %d.%m.%Y | %H:%M:%S ]", time.localtime())}: Raised ImportError: {error.msg}')
#         raise SystemExit


notes_names = os.listdir(f'{notebook_path}\\\\notes\\\\notes')

ENC_KEY = ''', '''
with open(f'{notebook_path}\\\\conf\\\\pd', 'rb') as file:
    secretsPass = decrypt(file.read())

font_size_label = settings['fontSize']['label']
font_size_button = settings['fontSize']['button']
font_size_optionMenu = settings['fontSize']['optionMenu']
tb_state = 'disabled'
secret_tb_state = 'disabled'
secrets_locked = True
# creating main app
app = ctk.CTk()
app.title(lang['title'])
app.wm_iconbitmap(f'{notebook_path}\\\\conf\\\\nb.ico')
app.protocol('WM_DELETE_WINDOW', confirm)
app.attributes('-topmost', settings['isTopmost'])
ctk.set_appearance_mode(settings['appearanceMode'])
ctk.set_default_color_theme(settings['colorTheme'])
app.bind('<KeyPress>', commands)
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
screen_scaling = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
app_width = int(screen_width * 40 / 100)
app_height = int(screen_height * 60 / 100)

bg_for_frames = '#2B2B2B' if ctk.get_appearance_mode() == 'Dark' else '#DBDBDB'

# first launch cycle for adding secrets password
while not secretsPass:
    inp = ctk.CTkInputDialog(title=lang['dia']['passAdd'][0], text=lang['dia']['passAdd'][1])
    password = inp.get_input()
    if not password:
        mb.showerror(lang['err']['noPass'][0], lang['err']['noPass'][1])
        continue
    if len(password) < 4:
        mb.showerror(lang['err']['shortPass'][0], lang['err']['shortPass'][1])
        inp.destroy()
        continue
    else:
        secretsPass = password
        os.system(f'attrib -h {notebook_path}\\\\conf\\\\pd')
        with open(f'{notebook_path}\\\\conf\\\\pd', 'wb') as file:
            file.write(encrypt(password))
        os.system(f'attrib +h {notebook_path}\\\\conf\\\\pd')
        del password
        mb.showinfo(lang['mb']['inf']['passAdded'][0], lang['mb']['inf']['passAdded'][1])

ctk.CTkLabel(master=app, text='Created by ArTred', font=('Segoe print', 9),
             text_color='#646464').pack(side='bottom', padx=5, pady=0, anchor='se')

# creating tab switcher
switch = ctk.CTkSegmentedButton(master=app, values=lang['gui']['avTabs'],
                                font=('Arial', settings['fontSize']['optionMenu']), command=change_page)
switch.set(lang['gui']['avTabs'][0])
switch.pack()

# creating basic frames
fr_notes = ctk.CTkFrame(master=app)
fr_notes.bind('<Button-1>', lambda e: fr_notes.focus())
fr_notes.pack(padx=10, fill='both', expand=True)
fr_lockscreen = ctk.CTkFrame(master=app)
fr_lockscreen.bind('<Button-1>', lambda e: fr_lockscreen.focus())
fr_secrets = ctk.CTkFrame(master=app)
fr_secrets.bind('<Button-1>', lambda e: fr_secrets.focus())
fr_settings = ctk.CTkScrollableFrame(master=app)

current_page = fr_notes

# tab Заметки {
panel_notes_top = Frame(master=fr_notes, bg=bg_for_frames)
panel_notes_top.pack(padx=15, pady=15, fill='x')
panel_notes_bottom = Frame(master=fr_notes, bg=bg_for_frames)
panel_notes_bottom.pack(side='bottom', padx=15, pady=10, fill='x')

ctk.CTkLabel(master=panel_notes_top, text=lang['gui']['l1'], font=('Arial', font_size_label),
             anchor='w').pack(side='left')
name = ctk.StringVar()
bas_notes = ctk.CTkOptionMenu(master=panel_notes_top, font=('Arial', font_size_optionMenu), variable=name, width=x(25),
                              command=select_value, corner_radius=9)
bas_current = None
bas_notes.set(lang['gui']['nChsn'])
bas_notes.pack(side='left', padx=15, ipadx=5)

l1 = ctk.CTkLabel(master=panel_notes_top, text=':', font=('Arial', font_size_label), anchor='w')
# l1.pack(side='left')

chapters_cmb = ctk.CTkOptionMenu(master=panel_notes_top, values=[], corner_radius=9, state='disabled', width=0,
                                      command=seek_to_chapter)
# chapters_cmb.pack(side='left', ipadx=10, padx=10)

note_actions_opt = ctk.CTkOptionMenu(master=panel_notes_top,
                                     values=lang['gui']['not']['actList'],
                                     font=('Segoe UI Emoji', font_size_optionMenu), width=0, state='disabled', command=note_action,
                                     corner_radius=9)
note_actions_opt.pack(side='right')
note_actions_opt.set(lang['gui']['actBtn'])

# make_it_secret_btn = ctk.CTkButton(master=panel_notes_top, text='⭢🔒', font=('Segoe UI Emoji', font_size_button), width=0,
#                                    state='disabled', command=make_it_secret, corner_radius=9)
# make_it_secret_btn.pack(side='right')

# remind_btn = ctk.CTkButton(master=panel_notes_top, text='🔔', font=('Segoe UI Emoji', font_size_button), width=0,
#                            state='disabled', command=remind_win, corner_radius=9)
# remind_btn.pack(side='right', padx=15)
# del_btn = ctk.CTkButton(master=panel_notes_top, text='🗑', font=('Segoe UI Emoji', font_size_button), width=0,
#                         state='disabled', command=delete, corner_radius=9)
# del_btn.pack(side='right')
# save_btn = ctk.CTkButton(master=panel_notes_top, text='💾', font=('Segoe UI Emoji', font_size_button), width=0,
#                          state='disabled', command=save, corner_radius=9)
# save_btn.pack(side='right', padx=15)
# rename_btn = ctk.CTkButton(master=panel_notes_top, text='🖊', font=('Segoe UI Emoji', font_size_button), width=0,
#                            state='disabled', command=rename_note, corner_radius=9)
# rename_btn.pack(side='right')
add_btn = ctk.CTkButton(master=panel_notes_top, text=' + ', font=('Arial', font_size_button), width=0,
                        command=create_note, corner_radius=9)
add_btn.pack(side='right', padx=15)

av_chapters = {}


tb = ctk.CTkTextbox(master=fr_notes, font=('Calibri', font_size_optionMenu + 1), corner_radius=10, state='disabled', wrap='word')
tb.pack(padx=15, fill='both', expand=True)

size_lbl = ctk.CTkLabel(master=panel_notes_bottom, text='', font=('Arial', font_size_optionMenu), text_color='#969696')
if settings['showSize']:
    size_lbl.pack(side='left')

date_state = 'changed'
date = ctk.CTkLabel(master=panel_notes_bottom, text='', font=('Arial', font_size_optionMenu), justify='right',
                    text_color='#969696')
date.bind('<Button-3>', changed_crated_toggle)
date.pack(side='right')
# } tab Заметки


# lockscreen {
group_lockscreen = Frame(master=fr_lockscreen, bg=bg_for_frames)
group_lockscreen.grid(row=0, column=0)
ctk.CTkLabel(master=group_lockscreen, text=lang['gui']['sec']['ls']['l'], font=('Arial', font_size_label)).grid(row=0, column=0,
                                                                                                   pady=15)
pass_entry_row = Frame(master=group_lockscreen, bg=bg_for_frames)
pass_entry_row.grid(row=1, column=0)
secrets_password_ent = ctk.CTkEntry(master=pass_entry_row, font=('Arial', font_size_optionMenu + 1), width=x(40),
                                    show='●')
secrets_password_ent.grid(row=0, column=0)
secrets_password_ent.bind('<Return>', verify_user)
lcscreen_show = ctk.CTkCheckBox(master=pass_entry_row, text='👁', onvalue=True, offvalue=False,
                                font=('Segoe UI Emoji', font_size_label), width=0,
                                command=lockscreen_show)
lcscreen_show.grid(row=0, column=1, padx=x(2), sticky='e')
verify = ctk.CTkButton(master=group_lockscreen, text=lang['gui']['sec']['ls']['b'], font=('Arial', font_size_button),
                       corner_radius=9, command=verify_user)
verify.grid(row=2, column=0, pady=15)

fr_lockscreen.grid_rowconfigure(0, weight=1)
fr_lockscreen.grid_columnconfigure(0, weight=1)
# } lockscreen


# tab Секреты {
secrets_names = os.listdir(f'{notebook_path}\\\\notes\\\\secrets')

panel_secrets_top = Frame(master=fr_secrets, bg=bg_for_frames)
panel_secrets_top.pack(padx=15, pady=15, fill='x')
panel_secrets_bottom = Frame(master=fr_secrets, bg=bg_for_frames)
panel_secrets_bottom.pack(side='bottom', padx=15, pady=10, fill='x')

ctk.CTkLabel(master=panel_secrets_top, text=lang['gui']['l1'], font=('Arial', font_size_label),
             anchor='w').pack(side='left')
secret_name = ctk.StringVar()
secret_notes = ctk.CTkOptionMenu(master=panel_secrets_top, font=('Arial', font_size_optionMenu), variable=secret_name,
                                 width=x(25), corner_radius=9, command=select_value)
secret_current = None
secret_notes.set(lang['gui']['nChsn'])
secret_notes.pack(side='left', padx=15, ipadx=10)

# secret_del_btn = ctk.CTkButton(master=panel_secrets_top, text='🗑', font=('Segoe UI Emoji', font_size_button), width=0,
#                                corner_radius=9, command=delete, state='disabled')
# secret_del_btn.pack(side='right')
# secret_save_btn = ctk.CTkButton(master=panel_secrets_top, text='💾', font=('Segoe UI Emoji', font_size_button),
#                                 width=0, corner_radius=9, command=save, state='disabled')
# secret_save_btn.pack(side='right', padx=15)
# secret_rename_btn = ctk.CTkButton(master=panel_secrets_top, text='🖊️', font=('Segoe UI Emoji', font_size_button),
#                                   width=0, corner_radius=9, command=rename_note, state='disabled')
# secret_rename_btn.pack(side='right')
# secret_lock = ctk.CTkButton(master=panel_secrets_top, text='🔒', font=('Segoe UI Emoji', font_size_button), width=0,
#                             corner_radius=9, command=lock)
# secret_lock.pack(side='right')
secret_actions_opt = ctk.CTkOptionMenu(master=panel_secrets_top,
                                     values=lang['gui']['sec']['sec']['actList'],
                                     font=('Segoe UI Emoji', font_size_optionMenu), width=0, state='disabled', command=note_action,
                                     corner_radius=9)
secret_actions_opt.pack(side='right')
secret_actions_opt.set(lang['gui']['actBtn'])

secret_add_btn = ctk.CTkButton(master=panel_secrets_top, text=' + ', font=('Arial', font_size_button), width=0,
                               corner_radius=9, command=create_note)
secret_add_btn.pack(side='right', padx=15)

secret_tb = ctk.CTkTextbox(master=fr_secrets, corner_radius=10, state='disabled', wrap='word')
secret_tb.pack(padx=15, fill='both', expand=True)

secret_date_state = 'changed'
secret_date = ctk.CTkLabel(master=panel_secrets_bottom, text='', font=('Arial', font_size_optionMenu),
                           justify='left', text_color='#969696')
secret_date.bind('<Button-3>', changed_crated_toggle)
secret_date.pack(side='right')
# } tab Секреты


sorting('both')


# tab Настройки {
rows = [ctk.CTkFrame(master=fr_settings) for _ in range(10)]
for row in rows:
    row.pack(padx=10, pady=15, fill='x')
ctk.CTkLabel(master=rows[0], text=lang['gui']['set'][0][0], font=('Arial', font_size_label)).pack(side='left')
change_btn = ctk.CTkButton(master=rows[0], text=lang['gui']['set'][0][1], font=('Arial', font_size_button),
                           command=change_password, width=0, corner_radius=9)
change_btn.pack(side='right', ipadx=10)

ctk.CTkLabel(master=rows[1], text=lang['gui']['set'][1][0], font=('Arial', font_size_label)).pack(side='left')
sort_opt = ctk.CTkOptionMenu(master=rows[1], values=lang['gui']['set'][1][1],
                             font=('Arial', font_size_optionMenu), width=0, corner_radius=9, command=set_sorting)
sort_opt.pack(side='right', ipadx=10)
match settings['sorting']:
    case 'z-a':
        sort_opt.set(lang['gui']['set'][1][1][1])
    case 'newFirst':
        sort_opt.set(lang['gui']['set'][1][1][2])
    case 'oldFirst':
        sort_opt.set(lang['gui']['set'][1][1][3])

ctk.CTkLabel(master=rows[2], text=lang['gui']['set'][2][0], font=('Arial', font_size_label)).pack(side='left')
font_opt = ctk.CTkOptionMenu(master=rows[2], values=lang['gui']['set'][2][1],
                             font=('Arial', font_size_optionMenu), width=0, corner_radius=9, command=set_font_size)
font_opt.pack(side='right', ipadx=10)

match settings['fontSize']['str']:
    case 'medium':
        font_opt.set(lang['gui']['set'][2][1][1])
    case 'large':
        font_opt.set(lang['gui']['set'][2][1][1])

ctk.CTkLabel(master=rows[3], text=lang['gui']['set'][3][0], font=('Arial', font_size_label)).pack(side='left')
theme_opt = ctk.CTkOptionMenu(master=rows[3], values=lang['gui']['set'][3][1],
                              font=('Arial', font_size_optionMenu), width=0, corner_radius=9, command=set_theme)
theme_opt.pack(side='right', ipadx=10)

match settings['appearanceMode']:
    case 'Dark':
        theme_opt.set(lang['gui']['set'][3][1][1])
    case 'System':
        theme_opt.set(lang['gui']['set'][3][1][2])

ctk.CTkLabel(master=rows[4], text=lang['gui']['set'][4][0], font=('Arial', font_size_label)).pack(side='left')
color_opt = ctk.CTkOptionMenu(master=rows[4], values=lang['gui']['set'][4][1],
                              font=('Arial', font_size_optionMenu), width=0, corner_radius=9, command=set_color_theme)
color_opt.pack(side='right', ipadx=10)


if settings['colorTheme'] == 'blue':
    color_opt.set(lang['gui']['set'][4][1][0])

elif settings['colorTheme'] == 'green':
    color_opt.set(lang['gui']['set'][4][1][1])

elif settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\red.json':
    color_opt.set(lang['gui']['set'][4][1][2])

elif settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\yellow.json':
    color_opt.set(lang['gui']['set'][4][1][3])

elif settings['colorTheme'] == f'{notebook_path}\\\\custom_colors\\\\purple.json':
    color_opt.set(lang['gui']['set'][4][1][4])


ctk.CTkLabel(master=rows[5], text=lang['gui']['set'][5], font=('Arial', font_size_label)).pack(side='left')
start_sw = ctk.CTkSwitch(master=rows[5], onvalue=True, offvalue=False, text=lang['gui']['n'], font=('Arial', font_size_label),
                         width=0, command=set_start)
if settings['startLast']:
    start_sw.configure(text=lang['gui']['y'])
    start_sw.select()
start_sw.pack(side='right')
check_start()

ctk.CTkLabel(master=rows[6], text=lang['gui']['set'][6], font=('Arial', font_size_label)).pack(side='left')
topmost_sw = ctk.CTkSwitch(master=rows[6], onvalue=True, offvalue=False, text=lang['gui']['n'], font=('Arial', font_size_label),
                           width=0, command=set_topmost)
if settings['isTopmost']:
    topmost_sw.configure(text=lang['gui']['y'])
    topmost_sw.select()
topmost_sw.pack(side='right')

ctk.CTkLabel(master=rows[7], text=lang['gui']['set'][7], font=('Arial', font_size_label)).pack(side='left')
show_size_sw = ctk.CTkSwitch(master=rows[7], onvalue=True, offvalue=False, text=lang['gui']['n'], font=('Arial', font_size_label),
                             width=0, command=set_show_size)
if settings['showSize']:
    show_size_sw.configure(text=lang['gui']['y'])
    show_size_sw.select()
show_size_sw.pack(side='right')

ctk.CTkLabel(master=rows[8], text=lang['gui']['set'][8][0], font=('Arial', font_size_label)).pack(side='left')
chapters_view_opt = ctk.CTkOptionMenu(master=rows[8], values=lang['gui']['set'][8][1], font=('Arial', font_size_optionMenu), width=0,
                                      corner_radius=9, command=set_chapter_pattern)
chapters_view_opt.pack(side='right')

match settings['chapterPattern']:
    case ">":
        chapters_view_opt.set(lang['gui']['set'][8][1][1])
    case "*":
        chapters_view_opt.set(lang['gui']['set'][8][1][2])

ctk.CTkLabel(master=rows[9], text=lang['gui']['set'][9][0], font=('Arial', font_size_label)).pack(side='left')
lang_opt = ctk.CTkOptionMenu(master=rows[9], values=lang['gui']['set'][9][1], font=('Arial', font_size_optionMenu), width=0,
                             corner_radius=9, command=set_lang)
lang_opt.pack(side='right')

match settings['lang']:
    case 'ru':
        lang_opt.set(lang['gui']['set'][9][1][1])
    case 'pl':
        lang_opt.set(lang['gui']['set'][9][1][2])


if settings['appGeometry'] == 'zoomed':
    app_state = 'zoomed'
    app.after(50, lambda: app.state('zoomed'))
else:
    app_state = 'normal'
    app.wm_geometry(settings['appGeometry'])
if settings['isTopmost']:
    Thread(target=app_state_check, daemon=True).start()

app.mainloop()
''']

USERNAME = os.getlogin()
system_type = platform.system()
# if system_type == 'Windows':
WD = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook'
# elif system_type == 'Linux':
#     WD = '~/Notebook'


def start_building():
    global WD, USERNAME
    # wd = WD
    app.protocol('WM_DELETE_WINDOW', lambda: ...)
    sb.configure(value=80)
    try:
        os.mkdir(WD)
    except FileExistsError:
        pass
    with open(WD+'\\nb.ico', 'wb') as f:
        f.write(ICON)
    with open(WD+'\\temp.py', 'a') as file:
        file.write(main_script[0])
        file.write(str(os.urandom(32)))
        file.write('\nENC_IV = ')
        file.write(str(os.urandom(16)))
        file.write(main_script[1])
    pyinstaller_path = os.path.join(os.getcwd(), 'compiler')
    sys.path.append(pyinstaller_path)
    process = subprocess.Popen(
        [
            sys.executable, os.path.join(pyinstaller_path, '__main__.py'),
            WD+'\\temp.py',
            '--onefile',
            '--noconsole',
            '-n=NoteBook',
            f'--icon={WD}\\nb.ico',
            f'--specpath={WD}'
        ]
        )
    process.wait()
    # while not process.poll():
    #     sleep(.5)
    # process.terminate()
    # process.kill()
    os.rename('dist\\NoteBook.exe', WD+'\\Notebook.exe')
    status_lbl.configure(text='Status: Deleting temporary files...')
    # sleep(60)
    os.remove(WD+'\\temp.py')
    os.remove(WD+'\\NoteBook.spec')
    shutil.rmtree('build')
    shutil.rmtree('dist')
    sb.configure(value=82)

###

    status_lbl.configure(text='Status: Creating needed directories...')
    WD = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\'
    os.mkdir(WD+'notes')
    os.mkdir(WD+'notes\\'+'notes')
    os.mkdir(WD+'notes\\'+'secrets')
    os.mkdir(WD+'conf')
    os.mkdir(WD+'conf\\'+'uicolors')
    os.mkdir(WD+'conf\\'+'lang')
    sb.configure(value=87)

###

    status_lbl.configure(text='Status: Creating configuration files...')
    os.rename(f'{WD}\\nb.ico', f'{WD}\\conf\\nb.ico')
    WD += 'conf\\'
    with open(WD+'debug.log', 'w') as file:
        file.write('')
    with open(WD+'pd', 'w') as file:
        file.write('')
    os.system(f'attrib +h {WD+"pd"}')
    s = json.loads(DEFAULT_SETTINGS)
    s['lang'] = lang.get()
    with open(WD+'settings.json', 'w') as f:
        f.write(json.dumps(s, indent=4))
    sb.configure(value=90)
    
###

    status_lbl.configure(text='Status: Installing language packs...')
    WD += 'lang\\'
    with open(WD+'en.json', 'w') as f:
        f.write(LANG_EN)
    with open(WD+'pl.json', 'w') as f:
        f.write(LANG_PL)
    with open(WD+'ru.json', 'w') as f:
        f.write(LANG_RU)
    sb.configure(value=93)

###

    status_lbl.configure(text='Status: Installing color themes...')
    WD = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\conf\\uicolors\\'
    with open(WD+'purple.json', 'w') as f:
        f.write(PURPLE)
    with open(WD+'yellow.json', 'w') as f:
        f.write(YELLOW)
    with open(WD+'red.json', 'w') as f:
        f.write(RED)
    sb.configure(value=96)

###

    status_lbl.configure(text='Status: Creating shortcut...')
    import winshell

    desktop_path = winshell.desktop()
    shortcut_path = os.path.join(desktop_path, "NoteBook.lnk")
    with winshell.shortcut(shortcut_path) as link:
        link.path = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\NoteBook.exe'
        link.icon = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\NoteBook.exe'
    sb.configure(value=100)

###

    status_lbl.configure(text='Status: Installation process finished successfully!\nThe app is ready to use')
    pr_btn.pack_forget()
    nx_btn.pack_forget()
    f_btn.pack(side='right')
    app.protocol('WM_DELETE_WINDOW', app.destroy)
    

def next_frame():
    global cf
    match cf:
        case 0:
            fr0.pack_forget()
            fr1.pack(expand=True, fill='both', padx=10)
            sb.configure(value=25)
            s_btn.pack_forget()
            nx_btn.pack(side='right')
            pr_btn.pack(side='right')
            cf = 1
        case 1:
            fr1.pack_forget()
            fr2.pack(expand=True, fill='both', padx=10)
            if not isagree.get():
                nx_btn.configure(state='disabled')
            sb.configure(value=50)
            cf = 2
        case 2:
            fr2.pack_forget()
            fr3.pack(expand=True, fill='both', padx=10)
            sb.configure(value=75)
            nx_btn.configure(state='disabled')
            pr_btn.configure(state='disabled')
            cf = 3
            threading.Thread(target=start_building).start()
            # start_building()
            
def prev_frame():
    global cf
    match cf:
        case 2:
            fr2.pack_forget()
            fr1.pack(expand=True, fill='both', padx=10)
            sb.configure(value=25)
            cf = 1
        case 1:
            fr1.pack_forget()
            fr0.pack(expand=True, fill='both', padx=10)
            sb.configure(value=0)
            s_btn.pack(side='right')
            nx_btn.pack_forget()
            pr_btn.pack_forget()
            cf = 0

def change_agreement():
    if isagree.get():
        nx_btn.configure(state='normal')
    else:
        nx_btn.configure(state='disabled')


def finish_installation():
    app.destroy()
    exit(0)

app = tk.Tk()
app.title('NoteBook installer')
app.geometry('400x300')
app.resizable(False, False)
# app.configure(background='#ebf6f9')

cf = 0

fsb = tk.Frame(app)
fsb.pack(side='top')
sb = ttk.Progressbar(fsb, length=380)
sb.pack(pady=5, padx=10)

fr0 = tk.Frame(app)
fr0.pack(expand=True, fill='both', padx=10)
fr00 = tk.Frame(fr0, width=150)
fr00.pack(side='left')
fr01 = tk.Frame(fr0, width=250)
fr01.pack(side='right')

img = Image.open('nt.png').convert("RGBA")
img = img.resize((150, 133), Image.Resampling.LANCZOS)
logo = ImageTk.PhotoImage(img)
tk.Label(fr00, image=logo, bg="#f0f0f0").pack(side='left')
ttk.Label(fr01, text='NoteBook installer', font=('Calibri', 20)).pack(anchor='w', pady=30)
fb = tk.Frame(app)
fb.pack(side='bottom', fill='x', padx=10, pady=5)
s_btn = ttk.Button(fb, text='Start', command=next_frame)
s_btn.pack(side='right')
nx_btn = ttk.Button(fb, text='Next', command=next_frame)
pr_btn = ttk.Button(fb, text='Previous', command=prev_frame)
f_btn = ttk.Button(fb, text='Finish', command=finish_installation)


fr1 = tk.Frame(app)
fr10 = tk.Frame(fr1)
fr10.pack(expand=True, fill='both', padx=60,  pady=10)
ttk.Label(fr10, text='Choose program language:', font=('Arial', 13)).pack(pady=15, anchor='w')

lang = tk.StringVar(fr10)
en = ttk.Radiobutton(fr10, text='English', variable=lang, value='en')
en.invoke()
en.pack(padx=30, pady=10, anchor='w')
pl = ttk.Radiobutton(fr10, text='Polski', variable=lang, value='pl')
pl.pack(padx=30, pady=10, anchor='w')
ru = ttk.Radiobutton(fr10, text='Русский', variable=lang, value='ru')
ru.pack(padx=30, pady=10, anchor='w')
ttk.Label(fr10, text='(it could be changed later in the app\'s settings)').pack(side='bottom')



fr2 = tk.Frame(app)
ttk.Label(fr2, text='User licensal agreement:', font=('Arial', 11)).pack(pady=7)
u_a = tk.Text(fr2, font=('Arial', 12), wrap='word', height=9)
u_a.insert('0.0', '''GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.

Preamble

The GNU General Public License is a free, copyleft license for
software and other kinds of works.

The licenses for most software and other practical works are designed
to take away your freedom to share and change the works. By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users. We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors. You can apply it to
your programs, too.

When we speak of free software, we are referring to freedom, not
price. Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights. Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received. You must make sure that they, too, receive
or can get the source code. And you must show them these terms so they
know their rights.

Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software. For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so. This is fundamentally incompatible with the aim of
protecting users' freedom to change the software. The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable. Therefore, we
have designed this version of the GPL to prohibit the practice for those
products. If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary. To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

The precise terms and conditions for copying, distribution and
modification follow.

TERMS AND CONDITIONS

0. Definitions.

"This License" refers to version 3 of the GNU General Public License.

"Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

"The Program" refers to any copyrightable work licensed under this
License. Each licensee is addressed as "you". "Licensees" and
"recipients" may be individuals or organizations.

To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy. The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

A "covered work" means either the unmodified Program or a work based
on the Program.

To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy. Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

To "convey" a work means any kind of propagation that enables other
parties to make or receive copies. Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License. If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

1. Source Code.

The "source code" for a work means the preferred form of the work
for making modifications to it. "Object code" means any non-source
form of a work.

A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form. A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities. However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work. For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

The Corresponding Source need not include anything that users can
regenerate automatically from other parts of the Corresponding Source.

The Corresponding Source for a work in source code form is that
same work.

2. Basic Permissions.

All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met. This License explicitly affirms your unlimited
permission to run the unmodified Program. The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work. This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force. You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright. Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

Conveying under any other circumstances is permitted solely under
the conditions stated below. Sublicensing is not allowed; section 10
makes it unnecessary.

3. Protecting Users' Legal Rights From Anti-Circumvention Law.

No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

4. Conveying Verbatim Copies.

You may convey verbatim copies of the license, and provide recipients with a copy of this License along
with the Program.

You may charge any price or no price for each copy that you convey, and
you may offer support or warranty protection for a fee.

5. Conveying Modified Source Versions.

You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

a) The work must carry prominent notices stating that you modified it,
and giving a relevant date.

b) The work must carry prominent notices stating that it is released
under this License and any conditions added under section 7. This
requirement modifies the requirement in section 4 to “keep intact all
notices”.

c) You must license the entire work, as a whole, under this License
to anyone who comes into possession of a copy. This License will
therefore apply, unmodified except as permitted by section 7, to the
whole of the work, and all its parts, regardless of how they are
packaged. This License gives no permission to license the work in any
other way, but it does not invalidate such permission if you have
separately received it.

d) If the work has interactive user interfaces, each must display
Appropriate Legal Notices; however, if the Program has interactive
interfaces that do not display Appropriate Legal Notices, your
work need not make them do so.

A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
“aggregate” if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation’s users
beyond what the individual works permit. Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

6. Conveying Non-Source Forms.

You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

a) Convey the object code in, or embodied in, a physical product
(including a physical distribution medium), accompanied by the
Corresponding Source fixed on a durable physical medium
customarily used for software interchange.

b) Convey the object code in, or embodied in, a physical product
(including a physical distribution medium), accompanied by a
written offer, valid for at least three years and valid for as
long as you offer spare parts or customer support for that product
model, to give anyone who possesses the object code either (1) a
copy of the Corresponding Source for all the software in the
product that is covered by this License, on a durable physical
medium customarily used for software interchange, for a price no
more than your reasonable cost of physically performing this
conveying of source, or (2) access to copy the
Corresponding Source from a network server at no charge.

c) Convey individual copies of the object code with a copy of the
written offer to provide the Corresponding Source. This
alternative is allowed only occasionally and noncommercially, and
only if you received the object code with such an offer, in accord
with subsection 6b.

d) Convey the object code by offering access from a designated place
(gratis or for a charge), and offer equivalent access to the
Corresponding Source in the same way through the same place at no
further charge. You need not require recipients to copy the
Corresponding Source along with the object code. If the place to
copy the object code is a network server, the Corresponding Source
may be on a different server (operated by you or a third party)
that supports equivalent copying facilities, provided you maintain
clear directions next to the object code saying where to find the
Corresponding Source. Regardless of what server hosts the
Corresponding Source, you remain obligated to ensure that it is
available for as long as needed to satisfy these requirements.

e) Convey the object code using peer-to-peer transmission, provided
you inform other peers where the object code and Corresponding
Source of the work are being offered to the general public at no
charge under subsection 6d.

A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

A “User Product” is either (1) a “consumer product”, which means any
tangible personal property which is normally used for personal,
family, or household purposes, or (2) anything designed or sold for
incorporation into a dwelling. In determining whether a product is a
consumer product, doubtful cases shall be resolved in favor of coverage.
For a particular product received by a particular user, “normally used”
refers to a typical or common use of that class of product, regardless
of the status of the particular user or of the way in which the
particular user actually uses, or expects or is expected to use, the
product. A product is a consumer product regardless of whether the
product has substantial commercial, industrial or non-consumer uses,
unless such uses represent the only significant mode of use of the
product.

“Installation Information” for a User Product means any methods,
procedures, authorization keys, or other information required to
install and execute modified versions of a covered work in that User
Product from a modified version of its Corresponding Source. The
information must suffice to ensure that the continued functioning of
the modified object code is in no case prevented or interfered with
solely because modification has been made.

If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information. But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or
updates for a work that has been modified or installed by the recipient,
or for the User Product in which it has been modified or installed. 
Access to a network may be denied when the modification itself
materially and adversely affects the operation of the network or
violates the rules and protocols for communication across the network.

Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.


By clicking "I accept terms of user agreement" you confirm that you have read, understood, and agree to the terms of this User License Agreement.''')
u_a.configure(state='disabled')
u_a.pack()

isagree = tk.BooleanVar()
iagree = ttk.Checkbutton(fr2, text='I accept terms of user agreement', offvalue=False, onvalue=True,
                         variable=isagree, command=change_agreement)
iagree.pack(padx=15, anchor='w')



fr3 = tk.Frame(app)
fr3.grid_columnconfigure(0, weight=1)
fr3.grid_rowconfigure(0, weight=1)

# fr30 = tk.Frame(fr3)
# fr30.grid(row=0, column=0)
status_lbl = ttk.Label(fr3, text='Status: Installation started', font=('Arial', 12))
status_lbl.grid(row=0, column=0)


app.mainloop()
