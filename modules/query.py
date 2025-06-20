load_query_des = """SELECT
    SIIAPP.dbo.COM_Cot.ID
    ,CAST(SIIAPP.dbo.COM_Cot.DATE_REP AS DATE) 
    ,UPPER(SIIAPP.dbo.COM_Cot.DATE_MONTH)
    ,SIIAPP.dbo.COM_Cot.COT_ID
    ,SIIAPP.dbo.COM_Cot.PRIO
    ,SIIAPP.dbo.COM_Cot.C_NAME
    ,SIIAPP.dbo.COM_Cot.BRAND
    ,SIIAPP.dbo.COM_Cot.COM_RESP
    ,SIIAPP.dbo.COM_Cot.MADE_BY
    ,SIIAPP.dbo.COM_Cot.RELATION
    ,SIIAPP.dbo.COM_Cot.QUANT_PROD
    ,SIIAPP.dbo.COM_Cot.COMPANY
    ,SIIAPP.dbo.COM_Cot.TRANS_STATE
    ,SIIAPP.dbo.COM_Cot.COT_STATE
    ,SIIAPP.dbo.COM_Cot.DATE_DELIV
    ,SIIAPP.dbo.COM_Cot.DELIV_DAYS
    ,SIIAPP.dbo.COM_Cot.DATE_CLIENT_SEND
    ,SIIAPP.dbo.COM_Cot.CLIENT_RESPON
    ,SIIAPP.dbo.COM_Cot.OBS
FROM SIIAPP.dbo.COM_Cot

            """
create_query_des = """
                INSERT INTO SIIAPP.dbo.COM_Cot (
                    COT_ID,
                    PRIO, 
                    C_NAME, 
                    BRAND, 
                    COM_RESP,
                    MADE_BY,
                    RELATION,
                    QUANT_PROD,
                    COMPANY
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

load_query_proy = """SELECT
    SIIAPP.dbo.COM_Proy.ID
    ,SIIAPP.dbo.COM_Proy.COT_STATE
    ,SIIAPP.dbo.COM_Proy.PROY_TYPE
    ,SIIAPP.dbo.COM_Proy.IN_DATE
    ,SIIAPP.dbo.COM_Proy.SOCIAL_REASON
    ,SIIAPP.dbo.COM_Proy.COUNTRY
    ,SIIAPP.dbo.COM_Proy.CLIENT_TYPE
    ,SIIAPP.dbo.COM_Proy.COMERCIAL
    ,SIIAPP.dbo.COM_Proy.PRODUCT
    ,SIIAPP.dbo.COM_Proy.NSOC
    ,SIIAPP.dbo.COM_Proy.QUANT
    ,SIIAPP.dbo.COM_Proy.UNIT_PRICE
    ,SIIAPP.dbo.COM_Proy.TOTAL_VALUE
    ,SIIAPP.dbo.COM_Proy.DEVELOP
    ,SIIAPP.dbo.COM_Proy.COT_COD
    ,SIIAPP.dbo.COM_Proy.SAMPLE_COD
    ,SIIAPP.dbo.COM_Proy.FINAL_STATE
    ,SIIAPP.dbo.COM_Proy.RESPONSIBLE
FROM SIIAPP.dbo.COM_Proy;
       """