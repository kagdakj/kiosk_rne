from flask import Flask, render_template, request
import timetable_gen
import re
import meal_gen

app = Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')



@app.route('/')
def home():
    with open("web/templates/main.html") as f:
        html = f.read()
    name = request.args.get('classroom')
    if name != None:

        #put table

        y,c = name.split('-')
        inc = timetable_gen.fetch(int(y),int(c),0)
        ren = re.sub("#sibaru",inc,html)
        inc = timetable_gen.fetch(int(y),int(c),1)
        ren = re.sub("#fuckin",inc,ren)

        print(ren)
        return ren
    else:
        return html


@app.route('/meal')
def meal():
    with open("web/templates/meal.html") as f:
        html = f.read()

    fetched_meal = meal_gen.meal_html()
    inc = fetched_meal[0]
    ren = re.sub("#timeline",inc,html)
    inc = fetched_meal[1]
    ren = re.sub("#meal_content",inc,ren)
    return ren

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=80)  #on my server the port shall be set to 80

    # On the computer the port value should be 8080
