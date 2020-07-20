from flask_wtf import FlaskForm
from wtforms import (SelectField, SelectMultipleField, BooleanField,
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
        if other_field.data is not None:
            if field.data <= other_field.data:
                raise ValidationError(self.message)


class NoneOfMultiple(object):
    def __init__(self, value, message=None):
        self.value = value
        if not message:
            message = "Seleccionar una opción válida."
        self.message = message

    def __call__(self, form, field):
        if any(item in field.data for item in self.value):
            raise ValidationError(self.message)


class SubmitForm(FlaskForm):
    indicators = [
        ("frequent_sep", "----- Tablas especiales -----"),
        ("tfm_prices", "Indicadores seleccionados de precios (mar-97, M)"),
        ("tfm_fiscal_gps_uyu_fssadj", "Cuentas fiscales: Sector público consolidado, ajustado FSS (ene-99, M)"),
        ("tfm_fiscal_nfps_uyu_fssadj", "Cuentas fiscales: Sector público no financiero, ajustado FSS (ene-99, M)"),
        ("tfm_fiscal_gc_uyu_fssadj", "Cuentas fiscales: Gobierno central-BPS, ajustado FSS (ene-99, M)"),
        ("tfm_labor_nsa", "Mercado laboral: tasas y personas (ene-06, M)"),
        ("tfm_wages_nsa", "Mercado laboral: salarios nominales y reales (ene-68, M)"),
        ("tfm_tb", "Comercio internacional: balanza comercial por país (ene-00, M)"),
        ("tfm_tot", "Comercio internacional: términos de intercambio (ene-05, M)"),
        ("rxr_custom", "Tipos de cambio reales, cálculos econuy (dic-79, M)"),
        ("commodity_index", "Índice econuy de precios de materias primas (ene-02, M)"),
        ("activity_sep", "----- Actividad económica -----"),
        ("naccounts_gas_con_nsa", "Cuentas nacionales: Demanda, precios constantes, series armonizadas (mar-05, T)"),
        ("naccounts_ind_con_nsa", "Cuentas nacionales: Oferta, precios constantes, series armonizadas (mar-05, T)"),
        ("naccounts_ind_con_idx_nsa", "Cuentas nacionales: Oferta, índice real, series armonizadas (mar-97, T)"),
        ("naccounts_ind_con_idx_sa", "Cuentas nacionales: Oferta, índice real, series desestacionalizadas (mar-97, T)"),
        ("naccounts_ind_cur_nsa", "Cuentas nacionales: Oferta, precios corrientes, series armonizadas (mar-05, T)"),
        ("naccounts_gdp_cur_nsa", "Cuentas nacionales: PBI, precios corrientes (mar-97, T)"),
        ("prices_sep", "----- Precios -----"),
        ("cpi", "Índice de precios al consumidor (ene-37, M)"),
        ("nxr_monthly", "Tipo de cambio, interbancario, mensual (abr-72, M)"),
        ("nxr_daily", "Tipo de cambio, interbancario, diario (3-ene-00, D)"),
        ("fiscal_sep", "----- Cuentas fiscales -----"),
        ("fiscal_nfps", "Cuentas fiscales: Sector público no financiero (ene-99, M)"),
        ("fiscal_gps", "Cuentas fiscales: Sector público consolidado (ene-99, M)"),
        ("fiscal_gc-bps", "Cuentas fiscales: Gobierno central-BPS (ene-99, M)"),
        ("fiscal_ancap", "Cuentas fiscales: ANCAP (ene-01, M)"),
        ("fiscal_antel", "Cuentas fiscales: ANTEL (ene-99, M)"),
        ("fiscal_ose", "Cuentas fiscales: OSE (ene-99, M)"),
        ("fiscal_ute", "Cuentas fiscales: UTE (ene-99, M)"),
        ("labor_sep", "----- Mercado laboral -----"),
        ("labor", "Mercado laboral: tasas de actividad, empleo y desempleo (ene-06, M)"),
        ("wages", "Mercado laboral: salarios (ene-68, M)"),
        ("external_sep", "----- Sector externo -----"),
        ("tb_x_prod_val", "Comercio internacional: Exportaciones por sector, valor (ene-00, M)"),
        ("tb_x_prod_vol", "Comercio internacional: Exportaciones por sector, volumen (ene-05, M)"),
        ("tb_x_prod_pri", "Comercio internacional: Exportaciones por sector, precio (ene-05, M)"),
        ("tb_x_dest_val", "Comercio internacional: Exportaciones por destino, valor (ene-00, M)"),
        ("tb_x_dest_vol", "Comercio internacional: Exportaciones por destino, volumen (ene-05, M)"),
        ("tb_x_dest_pri", "Comercio internacional: Exportaciones por destino, precio (ene-05, M)"),
        ("tb_m_sect_val", "Comercio internacional: Importaciones por tipo, valor (ene-00, M)"),
        ("tb_m_sect_vol", "Comercio internacional: Importaciones por tipo, volumen (ene-05, M)"),
        ("tb_m_sect_pri", "Comercio internacional: Importaciones por tipo, precio (ene-05, M)"),
        ("tb_m_orig_val", "Comercio internacional: Importaciones por origen, valor (ene-00, M)"),
        ("tb_m_orig_vol", "Comercio internacional: Importaciones por origen, volumen (ene-05, M)"),
        ("tb_m_orig_pri", "Comercio internacional: Importaciones por origen, precio (ene-05, M)"),
        ("rxr_official", "Tipos de cambio reales, BCU (ene-00, M)"),
        ("money_sep", "----- Moneda y banca -----"),
        ("reserves_chg", "Variación en las reservas del BCU (2-ene-13, D)")]
    operations = [("average", "Promedio"), ("sum", "Suma")]
    operations_res = [("average", "Reducir frecuencia: promedio"),
                      ("sum", "Reducir frecuencia: suma"),
                      ("end", "Reducir frecuencia: último período"),
                      ("upsample", "Aumentar frecuencia")]
    frequencies = [("A-DEC", "Anual"),
                   ("Q-DEC", "Trimestral"),
                   ("M", "Mensual"),
                   ("2W", "14 días"),
                   ("W", "Semanal")]
    chg_type = [("chg", "Variación porcentual"),
                ("diff", "Cambio")]
    chg_period = [("last", "Último período"),
                  ("inter", "Interanual"),
                  ("annual", "Anual")]
    seas_types = [("seas", "Desestacionalizado"),
                  ("trend", "Tendencia-ciclo")]
    seas_methods = [("loess", "Loess"),
                    ("ma", "Medias móviles"),
                    ("x13", "X13 ARIMA")]

    indicator = SelectField("Seleccionar tabla de datos", choices=indicators,
                            validators=[
                                DataRequired(),
                                NoneOf(["activity_sep", "prices_sep",
                                        "fiscal_sep", "labor_sep",
                                        "external_sep", "money_sep",
                                        "frequent_sep"],
                                       message="Seleccionar una tabla.")
                            ], id="indicator")
    start = DateField("Fecha inicial", format="%Y-%m-%d",
                      validators=[Optional()],
                      render_kw={"placeholder": "yyyy-mm-dd"})
    end = DateField("Fecha final", format="%Y-%m-%d",
                    validators=[Optional(), LaterDate("start")],
                    render_kw={"placeholder": "yyyy-mm-dd"})
    tail = IntegerField("Últimos x períodos", validators=[Optional()],
                        render_kw={"style": "width: 80px",
                                   "placeholder": 12})
    usd = BooleanField("Convertir a dólares")
    real = BooleanField("Deflactar")
    real_start = DateField("Fecha inicial", format="%Y-%m-%d",
                           validators=[Optional()],
                           render_kw={"placeholder": "yyyy-mm-dd"})
    real_end = DateField("Fecha final", format="%Y-%m-%d",
                         validators=[Optional(), LaterDate("real_start")],
                         render_kw={"placeholder": "yyyy-mm-dd"})
    gdp = BooleanField("Calcular % PBI")
    freq = BooleanField("Cambiar frequencia")
    frequency = SelectField("Frecuencia", choices=frequencies,
                            default="A-DEC")
    operation_res = SelectField("Método", choices=operations_res,
                                default="sum")
    cum = BooleanField("Acumular")
    periods = IntegerField("Períodos",
                           validators=[RequiredIf(cum=True,
                                                  message="Campo requerido.")],
                           render_kw={"style": "width: 80px",
                                      "placeholder": 12})
    operation = SelectField("Método", choices=operations, default="sum")
    base_index = BooleanField("Calcular índice base")
    base_index_start = DateField("Fecha inicial", format="%Y-%m-%d",
                                 validators=[
                                     RequiredIf(base_index=True,
                                                message="Campo requerido.")
                                 ],
                                 render_kw={"placeholder": "yyyy-mm-dd"})
    base_index_end = DateField("Fecha final", format="%Y-%m-%d",
                               validators=[Optional(),
                                           LaterDate("base_index_start")],
                               render_kw={"placeholder": "yyyy-mm-dd"})
    base_index_base = IntegerField("Valor base",
                                   validators=[
                                       RequiredIf(base_index=True,
                                                  message="Campo requerido.")
                                   ], render_kw={"style": "width: 80px",
                                                 "placeholder": 100})
    chg_diff = BooleanField("Calcular variaciones o diferencias")
    chg_diff_type = SelectField("Tipo", choices=chg_type, default="chg")
    chg_diff_period = SelectField("Períodos", choices=chg_period,
                                  default="last")
    seas = BooleanField("Desestacionalizar")
    seas_type = SelectField("Componente", choices=seas_types, default="seas")
    seas_method = SelectField("Método", choices=seas_methods, default="loess")
    some_cols = BooleanField("Filtrar series del cuadro")
    only_dl = BooleanField("Descargar datos sin visualizar")
    submit = SubmitField("Consultar", render_kw={"class": "btn btn-dark"})


class OrderForm(FlaskForm):
    order = [(str(i), str(i)) for i in range(1, 9)]
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
    chg_diff_order = SelectField("Calcular variaciones o diferencias",
                                 choices=order, validators=[DataRequired()],
                                 default="1")
    seas_order = SelectField("Desestacionalizar", choices=order,
                             validators=[DataRequired()], default="1")
    submit = SubmitField("Aceptar", render_kw={"class": "btn btn-dark"})


class ColumnForm(FlaskForm):
    choices = [("*", "Todas las series disponibles"), ("sep", "-----")]
    columns = SelectMultipleField(
        "Elegir series", choices=choices,
        validators=[DataRequired(),
                    NoneOfMultiple(["sep"])]
    )
    submit = SubmitField("Aceptar", render_kw={"class": "btn btn-dark"})

