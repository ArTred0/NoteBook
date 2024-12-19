import json
import os
import platform
import subprocess
import sys
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
# import shutil
import logging
import sys

from PIL import Image, ImageTk

from variables import *

logging.basicConfig(filename='debug.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception




USERNAME = os.getlogin()
system_type = platform.system()
# if system_type == 'Windows':
WD = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook'
# elif system_type == 'Linux':
#     WD = '~/Notebook'


def start_building():
    global WD, USERNAME
    app.protocol('WM_DELETE_WINDOW', lambda: ...)
    sb.configure(value=80)
    try:
        os.mkdir(WD)
    except FileExistsError:
        pass
    with open(WD+'\\nb.ico', 'wb') as f:
        f.write(ICON)
    if os.path.exists(WD+'\\NoteBook.py'):
        os.remove(WD+'\\NoteBook.py')
    with open(WD+'\\NoteBook.py', 'a', encoding='utf-8') as file:
        file.write(MAIN_SCRIPT[0])
        file.write(MAIN_SCRIPT[1])
        file.write(MAIN_SCRIPT[2])
    try:
        # process = subprocess.Popen(
        #     f'"{os.getcwd()}\\bin\\Scripts\\activate" & pyinstaller "{WD}\\temp.py" --onefile --noconsole -n=NoteBook --icon="{WD}\\nb.ico"',
        #     shell=True
        # )
        # process.wait()
        # os.rename('dist\\NoteBook.exe', WD+'\\Notebook.exe')
        # status_lbl.configure(text='Status: Deleting temporary files...')
        # os.remove(WD+'\\temp.py')
        # os.remove(WD+'\\NoteBook.spec')
        # shutil.rmtree('build')
        # shutil.rmtree('dist')
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
        with open(WD+'debug.log', 'w', encoding='utf-8') as file:
            file.write('')
        with open(WD+'pd', 'w', encoding='utf-8') as file:
            file.write('')
        os.system(f'attrib +h {WD+"pd"}')
        s = json.loads(DEFAULT_SETTINGS)
        s['lang'] = lang.get()
        with open(WD+'settings.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(s, indent=4))
        sb.configure(value=90)
###    
        status_lbl.configure(text='Status: Installing language packs...')
        WD += 'lang\\'
        with open(WD+'en.json', 'w', encoding='utf-8') as f:
            f.write(LANG_EN)
        with open(WD+'pl.json', 'w', encoding='utf-8') as f:
            f.write(LANG_PL)
        with open(WD+'ru.json', 'w', encoding='utf-8') as f:
            f.write(LANG_RU)
        sb.configure(value=93)
###    
        status_lbl.configure(text='Status: Installing color themes...')
        WD = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\conf\\uicolors\\'
        with open(WD+'purple.json', 'w', encoding='utf-8') as f:
            f.write(PURPLE)
        with open(WD+'yellow.json', 'w', encoding='utf-8') as f:
            f.write(YELLOW)
        with open(WD+'red.json', 'w', encoding='utf-8') as f:
            f.write(RED)
        sb.configure(value=96)
###    
        status_lbl.configure(text='Status: Creating shortcut...')
        import winshell
        desktop_path = winshell.desktop()
        shortcut_path = os.path.join(desktop_path, "NoteBook.lnk")
        with winshell.shortcut(shortcut_path) as link:
            link.path = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\NoteBook.py'
            link.icon = f'C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\conf\\nb.ico'
        sb.configure(value=100)
###    
        status_lbl.configure(text='Status: Installation process finished successfully!\nThe app is ready to use')
        pr_btn.pack_forget()
        nx_btn.pack_forget()
        ra_btn.pack(side='right')
        q_btn.pack(side='right')
        app.protocol('WM_DELETE_WINDOW', app.destroy)
    except Exception as exc:
        status_lbl.configure(text='Status: ERROR')
        app.protocol('WM_DELETE_WINDOW', app.destroy)
        mb.showerror(type(exc), exc)
    

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


def run_app():
    os.system(f"C:\\Users\\{USERNAME}\\AppData\\Local\\NoteBook\\NoteBook.exe")
    exit(0)

app = tk.Tk()
app.title('NoteBook installer')
app.geometry('400x300')
app.resizable(False, False)

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
q_btn = ttk.Button(fb, text='Quit', command=finish_installation)
ra_btn = ttk.Button(fb, text='Run App', command=run_app)


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

status_lbl = ttk.Label(fr3, text='Status: Installation started', font=('Arial', 12))
status_lbl.grid(row=0, column=0)

app.mainloop()
