from flask_wtf   import FlaskForm
from flask_babel import lazy_gettext as _l
#from wtforms     import SelectField
from wtforms     import SelectMultipleField, SubmitField, BooleanField
from wtforms.validators import DataRequired

class SelectForm(FlaskForm):
    #country = SelectField( _l('Country'), validators=[DataRequired()])
    fields = SelectMultipleField( _l('Type_of_fields'), validators=[DataRequired()])
    countries = SelectMultipleField( _l('Countries'), validators=[DataRequired()])
    submit = SubmitField( _l('plot'))
    
#def build_select_form(nations):
#    d = dict()
#    for nation in nations:
#        d[nation] = BooleanField(nation)
#    d['submit'] = SubmitField( _l('plot'))
#    return type('SForm', (FlaskForm,), d)