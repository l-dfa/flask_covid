from flask_wtf   import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms     import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

class SelectForm(FlaskForm):
    #country = SelectField( _l('Country'), validators=[DataRequired()])
    countries = SelectMultipleField( _l('Countries'))
    submit = SubmitField( _l('plot'))