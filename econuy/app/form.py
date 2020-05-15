from flask_wtf import FlaskForm
from wtforms import (SelectField, BooleanField,
                     SubmitField, IntegerField)
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, NoneOf, Optional, ValidationError


class RequiredIf(DataRequired):
    """Validator which makes a field required if another field is set
    and has a truthy value.

    Sources:
        - https://gist.github.com/devxoul/7638142#gistcomment-2601001
    """
    field_flags = ('requiredif',)

    def __init__(self, message=None, *args, **kwargs):
        super(RequiredIf).__init__()
        self.message = message
        self.conditions = kwargs

    def __call__(self, form, field):
        for name, data in self.conditions.items():
            other_field = form[name]
            if other_field is None:
                raise Exception(f"No field named {name} in form")
            if other_field.data == data and not field.data:
                DataRequired.__call__(self, form, field)
            Optional()(form, field)


class LaterDate(object):
    def __init__(self, other, message=None):
        self.other = other
        if not message:
            message = "Si se usa una fecha final, " \
                      "debe ser posterior a la inicial."
        self.message = message

    def __call__(self, form, field):
        other_field = form[self.other]
        if field.data <= other_field.data:
            raise ValidationError(self.message)


class SubmitForm(FlaskForm):
    indicators = [
        ("activity_sep", "----- Actividad económica -----"),
        ("naccounts_gas_con_nsa",
         "Cuentas nacionales: Demanda, precios constantes, series armonizadas (mar-05, T)"),
        ("naccounts_ind_con_nsa",
         "Cuentas nacionales: Oferta, precios constantes, series armonizadas (mar-05, T)"),
        ("naccounts_ind_con_idx_nsa",
         "Cuentas nacionales: Oferta, índice real, series armonizadas (mar-97, T)"),
        ("naccounts_ind_con_idx_sa",
         "Cuentas nacionales: Oferta, índice real, series "
         "desestacionalizadas (mar-97, T)"),
        ("naccounts_ind_cur_nsa",
         "Cuentas nacionales: Oferta, precios corrientes, series armonizadas (mar-05, T)"),
        ("naccounts_gdp_cur_nsa",
         "Cuentas nacionales: PBI, precios corrientes (mar-97, T)"),
        ("prices_sep", "----- Precios -----"),
        ("cpi", "Índice de precios al consumidor (ene-37, M)"),
        ("nxr_monthly", "Tipo de cambio, interbancario, mensual (abr-72, M)"),
        ("nxr_daily", "Tipo de cambio, interbancario, diario (3-ene-00, D)"),
        ("fiscal_sep", "----- Cuentas fiscales -----"),
        ("fiscal_nfps",
         "Cuentas fiscales: Sector público no financiero (ene-99, M)"),
        ("fiscal_gps",
         "Cuentas fiscales: Sector público consolidado (ene-99, M)"),
        (
            "fiscal_gc-bps",
            "Cuentas fiscales: Gobierno central-BPS (ene-99, M)"),
        ("fiscal_ancap", "Cuentas fiscales: ANCAP (ene-01, M)"),
        ("fiscal_antel", "Cuentas fiscales: ANTEL (ene-99, M)"),
        ("fiscal_ose", "Cuentas fiscales: OSE (ene-99, M)"),
        ("fiscal_ute", "Cuentas fiscales: UTE (ene-99, M)"),
        ("labor_sep", "----- Mercado laboral -----"),
        ("labor",
         "Mercado laboral: tasas de actividad, empleo y desempleo (ene-06, M)"),
        ("wages", "Mercado laboral: salarios (ene-68, M)"),
        ("external_sep", "----- Sector externo -----"),
        ("rxr_official", "Tipos de cambio reales, BCU (ene-00, M)"),
        ("rxr_custom", "Tipos de cambio reales, cálculos econ.uy (dic-79, M)"),
        ("commodity_index",
         "Índice econ.uy de precios de materias primas (ene-02, M)")]
    operations = [("average", "Promedio"), ("sum", "Suma")]
    operations_res = [("average", "Reducir frecuencia: promedio"),
                      ("sum", "Reducir frecuencia: suma"),
                      ("upsample", "Aumentar frecuencia")]
    frequencies = [("M", "Mensual"),
                   ("Q-DEC", "Trimestral"),
                   ("A-DEC", "Anual")]
    seas_types = [("seas", "Desestacionalizado"),
                  ("trend", "Tendencia-ciclo")]

    indicator = SelectField("Indicador", choices=indicators,
                            validators=[
                                DataRequired(),
                                NoneOf(["activity_sep", "prices_sep",
                                        "fiscal_sep", "labor_sep",
                                        "external_sep"],
                                       message="Seleccionar una tabla.")
                            ])
    usd = BooleanField("Convertir a dólares")
    real = BooleanField("Deflactar")
    real_start = DateField("Fecha inicial", format="%Y-%m-%d",
                           validators=[Optional()])
    real_end = DateField("Fecha final", format="%Y-%m-%d",
                         validators=[Optional(), LaterDate("real_start")])
    gdp = BooleanField("Calcular % PBI")
    freq = BooleanField("Cambiar frequencia")
    frequency = SelectField("Frecuencia", choices=frequencies,
                            default="A-DEC")
    operation_res = SelectField("Método", choices=operations_res,
                                default="sum")
    cum = BooleanField("Acumular")
    periods = IntegerField("Períodos",
                           validators=[RequiredIf(cum=True,
                                                  message="Campo requerido.")])
    operation = SelectField("Método", choices=operations, default="sum")
    base_index = BooleanField("Calcular índice base")
    base_index_start = DateField("Fecha inicial", format="%Y-%m-%d",
                                 validators=[
                                     RequiredIf(base_index=True,
                                                message="Campo requerido.")
                                 ])
    base_index_end = DateField("Fecha final", format="%Y-%m-%d",
                               validators=[Optional(),
                                           LaterDate("base_index_start")])
    base_index_base = IntegerField("Valor base",
                                   validators=[
                                       RequiredIf(base_index=True,
                                                  message="Campo requerido.")
                                   ])
    seas = BooleanField("Desestacionalizar")
    seas_type = SelectField("Tipo", choices=seas_types, default="seas")
    submit = SubmitField("Consultar")


class OrderForm(FlaskForm):
    order = [(str(i), str(i)) for i in range(1, 8)]
    usd_order = SelectField("Convertir a dólares", choices=order,
                            validators=[DataRequired()], default="1")
    real_order = SelectField("Deflactar", choices=order,
                             validators=[DataRequired()], default="1")
    gdp_order = SelectField("Calcular % PBI", choices=order,
                            validators=[DataRequired()], default="1")
    freq_order = SelectField("Cambiar frecuencia", choices=order,
                             validators=[DataRequired()], default="1")
    cum_order = SelectField("Acumular", choices=order,
                            validators=[DataRequired()], default="1")
    base_index_order = SelectField("Calcular índice base", choices=order,
                                   validators=[DataRequired()], default="1")
    seas_order = SelectField("Desestacionalizar", choices=order,
                             validators=[DataRequired()], default="1")
    submit = SubmitField("Consultar")
