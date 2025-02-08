from flask import Flask, render_template, request, send_file
from json import load
import os
SECRET_TOKEN = '[REDACTED]'

class challenge:
    def __init__(self, remaining: int, total: int, \
            category: str, title: str, desc: str, \
            attachment: str, flag: str, amount: int):
        self.remaining = remaining;
        self.total = total;
        self.category = category;
        self.title = title;
        self.desc = desc;
        self.attachment = attachment;
        self.flag = flag
        self.amount = amount

app = Flask(__name__)

remains = None
try:
    with open('status.txt', 'r') as status:
        remains = list(map(int, status.read().split(',')))
except FileNotFoundError:
    pass # fall through

descs = None
with open('desc.json', 'r') as desc:
    descs = load(desc)
assert type(descs) is list and len(descs) == 5, 'Corrupted json'
challenges = [challenge(e['total'] if not remains else remains[i],
                        e['total'], e['category'], e['title'],
                        e['desc'], e['att'], e['flag'], e['amount']) \
        for i, e in enumerate(descs)]
remains = [e.remaining for e in challenges]

@app.route('/')
def index():
    return render_template('index.html', table=challenges)

@app.route('/fill')
def fillup():
    try:
        challid = int(request.args.get('id'))
        return render_template('popup.html', chall=challenges[challid], challid=challid)
    except ValueError:
        return 'Can not decode id', 400
    except IndexError:
        return 'Corrupted id', 400
    except TypeError:
        return 'Lack of argument', 400

@app.route('/update')
def updateRemaining():
    try:
        challid = int(request.args.get('id'))
        if request.args.get('token') != SECRET_TOKEN:
            return 'No permission', 403
        remainder = int(request.args.get('remain'))
        if remainder > challenges[challid].total or remainder < 0:
            raise ValueError()
        challenges[challid].remaining = remainder
        remains[challid] = remainder
        with open('status.txt', 'w') as status:
            status.write(str(remains)[1:-1]) # strip [  ]
        return 'OK', 200
    except ValueError:
        return 'Can not decode id', 400
    except IndexError:
        return 'Corrupted id', 400
    except TypeError:
        return 'Lack of argument', 400

@app.route('/attachments')
def download():
    file = request.args.get('file')
    if file is None:
        return 'No file presented', 400
    if '/' in file: # restrict path
        return 'Corrupted file', 403
    file = 'assets/' + file
    # note send a directory will raise an error
    if not os.path.exists(file) or os.path.isdir(file):
        return 'File not found', 404
    return send_file(file)

@app.route('/verify')
def verify():
    try:
        challid = int(request.args.get('id'))
        correct = challenges[challid].flag
    except ValueError:
        return 'Can not decode id', 400
    except IndexError:
        return 'Corrupted id', 400
    except TypeError:
        return 'Lack of argument', 400
    toverify = request.args.get('flag')
    if toverify is None:
        return 'No flag provided', 400
    return str(toverify == correct), 200

@app.route('/favicon.ico')
def favicon():
    return send_file('static/icon.svg')

# this will not run when using gnunicorn as the server
if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=True)
