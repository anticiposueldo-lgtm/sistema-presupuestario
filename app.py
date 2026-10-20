# =====================================================================
# SECCIÓN 21: REPORTE DE EJECUCIÓN OFICIAL (TODAS LAS SOLAPAS)
# =====================================================================
elif opcion_menu == "📈 REPORTE DE EJECUCIÓN OFICIAL":
    st.subheader("📈 Módulo de Ejecución Presupuestaria - Reportes Oficiales")

    df_ejec_completo = leer_datos_gsheet(URL_READ_EJECUCION)

    if df_ejec_completo.empty:
        st.warning("⚠️ No se pudieron cargar los datos de la hoja de ejecución.")
    else:
        df_ejec_completo.columns = [str(c).strip().upper() for c in df_ejec_completo.columns]
        cols_e = df_ejec_completo.columns.tolist()

        def limpiar_monto_val(val):
            if pd.isna(val): return 0.0
            s = str(val).replace("$", "").replace(" ", "").strip()
            if not s or s.lower() == "nan": return 0.0
            if "," in s and "." in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except Exception:
                return 0.0

        c_sec_k = cols_e[0] if len(cols_e) > 0 else "SECRETARIA"
        c_sub_k = cols_e[1] if len(cols_e) > 1 else "SUBSECRETARÍA"
        c_dest_k = cols_e[2] if len(cols_e) > 2 else "DESTINO"
        c_obj = cols_e[3] if len(cols_e) > 3 else "OBJETO_GASTO" # Columna D
        c_partida = cols_e[4] if len(cols_e) > 4 else cols_e[5] # Columna E (Imputación)
        c_padre = cols_e[13] if len(cols_e) > 13 else cols_e[4] # Columna N (Cuenta Padre)

        c_pres = cols_e[6] if len(cols_e) > 6 else cols_e[6]
        c_dev = cols_e[7] if len(cols_e) > 7 else cols_e[6]
        c_ejec = cols_e[8] if len(cols_e) > 8 else cols_e[6]
        c_mod = cols_e[9] if len(cols_e) > 9 else cols_e[6]
        c_saldo = cols_e[10] if len(cols_e) > 10 else cols_e[6]

        df_validas = df_ejec_completo[
            df_ejec_completo[c_obj].notna() & 
            (df_ejec_completo[c_obj].astype(str).str.strip() != "") & 
            (df_ejec_completo[c_obj].astype(str).str.upper() != "NAN") &
            df_ejec_completo[c_padre].notna() & 
            (df_ejec_completo[c_padre].astype(str).str.strip() != "") & 
            (df_ejec_completo[c_padre].astype(str).str.upper() != "NAN") &
            df_ejec_completo[c_partida].notna() & 
            (df_ejec_completo[c_partida].astype(str).str.strip() != "") & 
            (df_ejec_completo[c_partida].astype(str).str.upper() != "NAN")
        ].copy()

        tab_ejec_1, tab_ejec_2, tab_ejec_3, tab_ejec_4, tab_ejec_5, tab_ejec_6 = st.tabs([
            "📊 Resumen por Destino (Matriz)",
            "🏛️ Desglose Escalonado por Destino",
            "📦 Totales por Objeto del Gasto",
            "🔍 Buscador y Control de Saldos",
            "📄 Exportación y Firmas (PDF)",
            "🏛️ Reporte por Finalidad y Función"
        ])

        # -------------------------------------------------------------
        # SOLAPA 1: MATRIZ DE DESTINOS VS OBJETOS
        # -------------------------------------------------------------
        with tab_ejec_1:
            st.markdown("##### 📊 Cuadro Resumen: Destinos vs. Objetos del Gasto")
            st.info("💡 Cada fila representa un **Destino** y cada columna un **Objeto del Gasto** con su respectivo total devengado.")

            if not df_validas.empty:
                df_validas["_DEV_NUM"] = df_validas[c_dev].apply(limpiar_monto_val)

                df_pivote = df_validas.pivot_table(
                    index=c_dest_k, 
                    columns=c_obj, 
                    values="_DEV_NUM", 
                    aggfunc="sum", 
                    fill_value=0.0
                ).reset_index()

                cols_obj_piv = [c for c in df_pivote.columns if c != c_dest_k]
                df_pivote_fmt = df_pivote.copy()
                for col in cols_obj_piv:
                    df_pivote_fmt[col] = df_pivote_fmt[col].map(lambda x: f"${x:,.2f}" if x > 0 else "$0.00")

                st.dataframe(df_pivote_fmt, use_container_width=True, hide_index=True)

                tot_matriz_gral = df_validas["_DEV_NUM"].sum()
                rows_matriz_html = ""
                for _, rw in df_pivote.iterrows():
                    dest_n = rw[c_dest_k]
                    rows_matriz_html += f'<tr><td style="text-align: left; padding-left: 8px; font-weight: bold;">{dest_n}</td>'
                    for c_o in cols_obj_piv:
                        val_c = rw[c_o]
                        rows_matriz_html += f'<td style="text-align: right;">${val_c:,.2f}</td>'
                    rows_matriz_html += '</tr>'

                headers_matriz_th = "".join([f'<th style="text-align: right;">{col}</th>' for col in cols_obj_piv])

                html_matriz_reporte = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @page {{ size: A4 landscape; margin: 12mm; }}
                        body {{ font-family: Arial, sans-serif; color: #000; margin: 0 auto; width: 100%; max-width: 1050px; }}
                        .m-box {{ border: 1px solid #000; padding: 10px; margin-bottom: 15px; background-color: #fff; }}
                        .t-hdr {{ width: 100%; border-collapse: collapse; }}
                        .t-hdr td {{ padding: 4px; vertical-align: middle; border: none; }}
                        .b-tot {{ border: 1px solid #000; background-color: #f5f5f5; text-align: center; }}
                        .tabla-datos {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; margin-bottom: 25px; }}
                        .tabla-datos th {{ border-bottom: 2px solid #000; padding: 6px 4px; font-weight: bold; background-color: #f2f2f2; }}
                        .tabla-datos td {{ border-bottom: 1px solid #e0e0e0; padding: 6px 4px; vertical-align: middle; }}
                        .resumen-final {{ border: 2px solid #000; padding: 15px; margin-top: 20px; background-color: #fafafa; text-align: center; font-size: 14px; page-break-inside: avoid; }}
                        .firmas-container {{ margin-top: 50px; width: 100%; page-break-inside: avoid; }}
                        .firma-box {{ width: 30%; float: left; text-align: center; border-top: 1px solid #000; padding-top: 5px; margin: 0 1.5%; font-size: 11px; font-weight: bold; }}
                    </style>
                </head>
                <body onload="window.print();">
                    <div class="m-box">
                        <table class="t-hdr">
                            <tr>
                                <td style="width: 25%; text-align: left; font-size: 10px;"><b>Municipalidad de Sunchales</b><br><span style="font-size: 8px; color: #555;">Ejecución de Egresos - Año 2026</span></td>
                                <td style="width: 50%; text-align: center;"><b>MATRIZ RESUMEN: DESTINOS VS OBJETOS</b><br><small>- Control Financiero -</small></td>
                                <td style="width: 25%;" class="b-tot"><small>Total General</small><br><b>${tot_matriz_gral:,.2f}</b></td>
                            </tr>
                        </table>
                    </div>
                    <table class="tabla-datos">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-left: 8px;">DESTINO</th>
                                {headers_matriz_th}
                            </tr>
                        </thead>
                        <tbody>
                            {rows_matriz_html}
                        </tbody>
                    </table>
                    <div class="resumen-final">
                        <b>TOTAL GENERAL DEVENGADO MUNICIPAL:</b> ${tot_matriz_gral:,.2f}
                    </div>
                    <div class="firmas-container">
                        <div class="firma-box">Responsable Presupuesto</div>
                        <div class="firma-box">Sec. Hacienda</div>
                        <div class="firma-box">Intendente</div>
                    </div>
                </body>
                </html>
                """

                st.download_button(
                    label="📥 Descargar Matriz Resumen Oficial (PDF/HTML)",
                    data=html_matriz_reporte,
                    file_name=f"Matriz_Resumen_Destinos_{time.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ No hay datos suficientes para generar la matriz.")

        # -------------------------------------------------------------
        # SOLAPA 2: DESGLOSE ESCALONADO POR DESTINO
        # -------------------------------------------------------------
        with tab_ejec_2:
            st.markdown("##### 🏛️ Desglose Escalonado por Destino")
            cf1, cf2, col_f3 = st.columns(3)
            sec_ops = sorted([str(x) for x in df_validas[c_sec_k].unique() if str(x).strip() != ""])

            with cf1:
                sec_s_ejec = st.selectbox("1. SECRETARÍA:", options=[""] + sec_ops, key="ejec_of_sec")

            df_ejec_f1 = df_validas[df_validas[c_sec_k].astype(str).str.strip().str.upper() == sec_s_ejec.strip().upper()] if sec_s_ejec else pd.DataFrame()
            sub_ops = sorted([str(x) for x in df_ejec_f1[c_sub_k].unique() if str(x).strip() != ""]) if not df_ejec_f1.empty else []

            with cf2:
                sub_s_ejec = st.selectbox("2. SUBSECRETARÍA:", options=[""] + sub_ops, key="ejec_of_sub")

            with col_f3:
                if sec_s_ejec and sub_s_ejec:
                    df_ejec_f2 = df_ejec_f1[df_ejec_f1[c_sub_k].astype(str).str.strip().str.upper() == sub_s_ejec.strip().upper()]
                    dest_ops = sorted([str(x) for x in df_ejec_f2[c_dest_k].unique() if str(x).strip() != ""])
                    dest_s_ejec = st.selectbox("3. DESTINO:", options=[""] + dest_ops, key="ejec_of_dest")
                else:
                    dest_s_ejec = st.selectbox("3. DESTINO:", options=[""], key="ejec_of_dest")

            if sec_s_ejec and sub_s_ejec and dest_s_ejec:
                df_f_oficial_ejec = df_ejec_f2[df_ejec_f2[c_dest_k].astype(str).str.strip().str.upper() == dest_s_ejec.strip().upper()].copy()

                df_f_oficial_ejec["_G_VAL"] = df_f_oficial_ejec[c_pres].apply(limpiar_monto_val)
                df_f_oficial_ejec["_H_VAL"] = df_f_oficial_ejec[c_dev].apply(limpiar_monto_val)
                df_f_oficial_ejec["_I_VAL"] = df_f_oficial_ejec[c_ejec].apply(limpiar_monto_val)
                df_f_oficial_ejec["_J_VAL"] = df_f_oficial_ejec[c_mod].apply(limpiar_monto_val)
                df_f_oficial_ejec["_K_VAL"] = df_f_oficial_ejec[c_saldo].apply(limpiar_monto_val)

                tot_devengado_val = df_f_oficial_ejec["_H_VAL"].sum()

                f_plan_ejec = []
                rows_html_esc = ""
                for obj, df_obj in df_f_oficial_ejec.groupby(c_obj):
                    tp_g = df_obj["_G_VAL"].sum()
                    tp_h = df_obj["_H_VAL"].sum()
                    tp_i = df_obj["_I_VAL"].sum()
                    tp_j = df_obj["_J_VAL"].sum()
                    tp_k = df_obj["_K_VAL"].sum()

                    f_plan_ejec.append({
                        "OBJETO / CUENTA / IMPUTACIÓN": f"<b>{obj}</b>",
                        "PRESUPUESTO": f"<b>${tp_g:,.2f}</b>",
                        "DEVENGADO": f"<b>${tp_h:,.2f}</b>",
                        "EJECUTADO": f"<b>${tp_i:,.2f}</b>",
                        "MODIFICACIONES": f"<b>${tp_j:,.2f}</b>",
                        "SALDO": f"<b>${tp_k:,.2f}</b>"
                    })
                    rows_html_esc += f'<tr style="font-weight: bold; background-color: #f9f9f5;"><td style="text-align: left; padding-left: 5px;">{obj}</td><td style="text-align: right;">${tp_g:,.2f}</td><td style="text-align: right;">${tp_h:,.2f}</td><td style="text-align: right;">${tp_i:,.2f}</td><td style="text-align: right;">${tp_j:,.2f}</td><td style="text-align: right;">${tp_k:,.2f}</td></tr>'

                    for pad, df_pad in df_obj.groupby(c_padre):
                        pad_g = df_pad["_G_VAL"].sum()
                        pad_h = df_pad["_H_VAL"].sum()
                        pad_i = df_pad["_I_VAL"].sum()
                        pad_j = df_pad["_J_VAL"].sum()
                        pad_k = df_pad["_K_VAL"].sum()

                        f_plan_ejec.append({
                            "OBJETO / CUENTA / IMPUTACIÓN": f"&nbsp;&nbsp;&nbsp;&nbsp;<b>{pad}</b>",
                            "PRESUPUESTO": f"<b>${pad_g:,.2f}</b>",
                            "DEVENGADO": f"<b>${pad_h:,.2f}</b>",
                            "EJECUTADO": f"<b>${pad_i:,.2f}</b>",
                            "MODIFICACIONES": f"<b>${pad_j:,.2f}</b>",
                            "SALDO": f"<b>${pad_k:,.2f}</b>"
                        })
                        rows_html_esc += f'<tr style="font-weight: bold;"><td style="text-align: left; padding-left: 20px;">{pad}</td><td style="text-align: right;">${pad_g:,.2f}</td><td style="text-align: right;">${pad_h:,.2f}</td><td style="text-align: right;">${pad_i:,.2f}</td><td style="text-align: right;">${pad_j:,.2f}</td><td style="text-align: right;">${pad_k:,.2f}</td></tr>'

                        for _, r in df_pad.iterrows():
                            vg = limpiar_monto_val(r.get(c_pres, 0))
                            vh = limpiar_monto_val(r.get(c_dev, 0))
                            vi = limpiar_monto_val(r.get(c_ejec, 0))
                            vj = limpiar_monto_val(r.get(c_mod, 0))
                            vk = limpiar_monto_val(r.get(c_saldo, 0))
                            partida_val = str(r.get(c_partida, ""))

                            f_plan_ejec.append({
                                "OBJETO / CUENTA / IMPUTACIÓN": f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{partida_val}",
                                "PRESUPUESTO": f"${vg:,.2f}",
                                "DEVENGADO": f"${vh:,.2f}",
                                "EJECUTADO": f"${vi:,.2f}",
                                "MODIFICACIONES": f"${vj:,.2f}",
                                "SALDO": f"${vk:,.2f}"
                            })
                            rows_html_esc += f'<tr><td style="text-align: left; padding-left: 40px;">{partida_val}</td><td style="text-align: right;">${vg:,.2f}</td><td style="text-align: right;">${vh:,.2f}</td><td style="text-align: right;">${vi:,.2f}</td><td style="text-align: right;">${vj:,.2f}</td><td style="text-align: right;">${vk:,.2f}</td></tr>'

                # Vista Previa Estética en la App
                st.markdown(f"""
                <div style="border: 1px solid #000; padding: 0px; border-radius: 2px; background-color: #fff; font-family: Arial, sans-serif;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="width: 25%; font-size: 11px; padding: 15px; border-right: 1px solid #000; text-align: left;"><b>Municipalidad de Sunchales</b><br><span style="font-size: 9px; color: #777;">Ejecución de Egresos - Año 2026</span></td>
                            <td style="width: 50%; text-align: center; padding: 15px; border-right: 1px solid #000; vertical-align: middle;"><h2 style="margin: 0; font-size: 16px; font-weight: bold;">REPORTE DE EJECUCIÓN POR DESTINO</h2><h4 style="margin: 4px 0 0 0; font-size: 12px; font-weight: normal;">- Desglose Escalonado -</h4></td>
                            <td style="width: 25%; text-align: center; background-color: #f5f5f5; vertical-align: middle;"><div style="font-size: 12px; font-weight: bold; border-bottom: 1px solid #000; padding: 4px 0;">Total Devengado</div><div style="font-size: 16px; font-weight: bold;">${tot_devengado_val:,.2f}</div></td>
                        </tr>
                    </table>
                    <div style="border-top: 1px solid #000; font-size: 11px; padding: 6px 10px;">
                        <b>SECRETARÍA:</b> {sec_s_ejec} | <b>SUBSECRETARÍA:</b> {sub_s_ejec} | <span style="float: right;"><b>DESTINO:</b> {str(dest_s_ejec).upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.write(pd.DataFrame(f_plan_ejec).to_html(escape=False, index=False), unsafe_allow_html=True)

                # HTML para impresión limpia sin letras de columnas
                html_reporte_escalonado = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @page {{ size: A4 landscape; margin: 12mm; }}
                        body {{ font-family: Arial, sans-serif; color: #000; margin: 0 auto; width: 100%; max-width: 1050px; }}
                        .m-box {{ border: 1px solid #000; padding: 10px; margin-bottom: 15px; background-color: #fff; }}
                        .t-hdr {{ width: 100%; border-collapse: collapse; }}
                        .t-hdr td {{ padding: 4px; vertical-align: middle; border: none; }}
                        .b-tot {{ border: 1px solid #000; background-color: #f5f5f5; text-align: center; }}
                        .tabla-datos {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; margin-bottom: 25px; }}
                        .tabla-datos th {{ border-bottom: 2px solid #000; padding: 6px 4px; font-weight: bold; background-color: #f2f2f2; text-align: right; }}
                        .tabla-datos th:first-child {{ text-align: left !important; padding-left: 8px; }}
                        .tabla-datos td {{ border-bottom: 1px solid #e0e0e0; padding: 6px 4px; vertical-align: middle; text-align: right; }}
                        .tabla-datos td:first-child {{ text-align: left !important; padding-left: 8px; }}
                        .resumen-final {{ border: 2px solid #000; padding: 15px; margin-top: 20px; background-color: #fafafa; text-align: center; font-size: 14px; page-break-inside: avoid; }}
                        .firmas-container {{ margin-top: 50px; width: 100%; page-break-inside: avoid; }}
                        .firma-box {{ width: 30%; float: left; text-align: center; border-top: 1px solid #000; padding-top: 5px; margin: 0 1.5%; font-size: 11px; font-weight: bold; }}
                    </style>
                </head>
                <body onload="window.print();">
                    <div class="m-box">
                        <table class="t-hdr">
                            <tr>
                                <td style="width: 25%; text-align: left; font-size: 10px;"><b>Municipalidad de Sunchales</b><br><span style="font-size: 8px; color: #555;">Ejecución de Egresos - Año 2026</span></td>
                                <td style="width: 50%; text-align: center;"><b>REPORTE DE EJECUCIÓN POR DESTINO (ESCALONADO)</b><br><small>- Control Financiero -</small></td>
                                <td style="width: 25%;" class="b-tot"><small>Total Devengado</small><br><b>${tot_devengado_val:,.2f}</b></td>
                            </tr>
                        </table>
                        <div style="border-top: 1px solid #000; font-size: 11px; padding-top: 6px; margin-top: 6px;">
                            <b>SECRETARÍA:</b> {sec_s_ejec} | <b>SUBSECRETARÍA:</b> {sub_s_ejec} | <span style="float: right;"><b>DESTINO:</b> {str(dest_s_ejec).upper()}</span>
                        </div>
                    </div>
                    <table class="tabla-datos">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-left: 8px;">OBJETO / CUENTA / IMPUTACIÓN</th>
                                <th>PRESUPUESTO</th>
                                <th>DEVENGADO</th>
                                <th>EJECUTADO</th>
                                <th>MODIFICACIONES</th>
                                <th>SALDO</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html_esc}
                        </tbody>
                    </table>
                    <div class="resumen-final">
                        <b>TOTAL DEVENGADO DESTINO ({str(dest_s_ejec).upper()}):</b> ${tot_devengado_val:,.2f}
                    </div>
                    <div class="firmas-container">
                        <div class="firma-box">Responsable Presupuesto</div>
                        <div class="firma-box">Sec. Hacienda</div>
                        <div class="firma-box">Intendente</div>
                    </div>
                </body>
                </html>
                """

                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 Descargar Reporte Escalonado Oficial por Destino (HTML/PDF)",
                    data=html_reporte_escalonado,
                    file_name=f"Desglose_Escalonado_{str(dest_s_ejec).replace(' ', '_')}_{time.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.info("💡 Seleccioná Secretaría, Subsecretaría y Destino arriba para desplegar el reporte.")
        # -------------------------------------------------------------
        # SOLAPA 3: TOTALES POR OBJETO DEL GASTO
        # -------------------------------------------------------------
        with tab_ejec_3:
            st.markdown("##### 📦 Consolidado de Egresos por Objeto del Gasto")
            df_validas["_H_VAL"] = df_validas[c_dev].apply(limpiar_monto_val)
            df_obj_res = df_validas.groupby(c_obj)["_H_VAL"].sum().reset_index()
            df_obj_res.columns = ["OBJETO DEL GASTO", "DEVENGADO ($)"]
            df_obj_res["DEVENGADO ($)"] = df_obj_res["DEVENGADO ($)"].map(lambda x: f"${x:,.2f}")
            st.dataframe(df_obj_res, use_container_width=True, hide_index=True)

        # -------------------------------------------------------------
        # SOLAPA 4: BUSCADOR GENERAL DE EGRESOS
        # -------------------------------------------------------------
        with tab_ejec_4:
            st.markdown("##### 🔍 Buscador General de Egresos")
            q_ejec = st.text_input("Buscar texto o partida:", key="busq_ejec_s3").strip()
            if q_ejec:
                mask_q = df_validas.astype(str).apply(lambda r: r.str.lower().str.contains(q_ejec.lower()).any(), axis=1)
                st.dataframe(df_validas[mask_q], use_container_width=True, hide_index=True)
            else:
                st.info("Escribí un criterio para buscar.")

        # -------------------------------------------------------------
        # SOLAPA 5: EXPORTACIÓN OFICIAL Y FIRMAS (CONSOLIDADO)
        # -------------------------------------------------------------
        with tab_ejec_5:
            st.markdown("##### 📄 Exportación Oficial Consolidada de Egresos")
            st.info("💡 Hacé clic abajo para descargar el reporte oficial completo con sus columnas financieras y firmas.")

            bloques_ejec_html = ""
            total_general_devengado = 0.0

            for (s_exp, sub_e, d_exp), df_g_exp in df_validas.groupby([c_sec_k, c_sub_k, c_dest_k]):
                rows_html_exp = ""
                tot_dev_dest = 0.0

                for obj, df_obj in df_g_exp.groupby(c_obj):
                    tp_g = sum(limpiar_monto_val(r.get(c_pres, 0)) for _, r in df_obj.iterrows())
                    tp_h = sum(limpiar_monto_val(r.get(c_dev, 0)) for _, r in df_obj.iterrows())
                    tp_i = sum(limpiar_monto_val(r.get(c_ejec, 0)) for _, r in df_obj.iterrows())
                    tp_j = sum(limpiar_monto_val(r.get(c_mod, 0)) for _, r in df_obj.iterrows())
                    tp_k = sum(limpiar_monto_val(r.get(c_saldo, 0)) for _, r in df_obj.iterrows())
                    tot_dev_dest += tp_h

                    rows_html_exp += f'<tr style="font-weight: bold; background-color: #f9f9f5;"><td style="text-align: left; padding-left: 5px;">{obj}</td><td style="text-align: right;">${tp_g:,.2f}</td><td style="text-align: right;">${tp_h:,.2f}</td><td style="text-align: right;">${tp_i:,.2f}</td><td style="text-align: right;">${tp_j:,.2f}</td><td style="text-align: right;">${tp_k:,.2f}</td></tr>'

                    for pad, df_pad in df_obj.groupby(c_padre):
                        pad_g = sum(limpiar_monto_val(r.get(c_pres, 0)) for _, r in df_pad.iterrows())
                        pad_h = sum(limpiar_monto_val(r.get(c_dev, 0)) for _, r in df_pad.iterrows())
                        pad_i = sum(limpiar_monto_val(r.get(c_ejec, 0)) for _, r in df_pad.iterrows())
                        pad_j = sum(limpiar_monto_val(r.get(c_mod, 0)) for _, r in df_pad.iterrows())
                        pad_k = sum(limpiar_monto_val(r.get(c_saldo, 0)) for _, r in df_pad.iterrows())

                        rows_html_exp += f'<tr style="font-weight: bold;"><td style="text-align: left; padding-left: 20px;">{pad}</td><td style="text-align: right;">${pad_g:,.2f}</td><td style="text-align: right;">${pad_h:,.2f}</td><td style="text-align: right;">${pad_i:,.2f}</td><td style="text-align: right;">${pad_j:,.2f}</td><td style="text-align: right;">${pad_k:,.2f}</td></tr>'

                        for _, rw in df_pad.iterrows():
                            vg = limpiar_monto_val(rw.get(c_pres, 0))
                            vh = limpiar_monto_val(rw.get(c_dev, 0))
                            vi = limpiar_monto_val(rw.get(c_ejec, 0))
                            vj = limpiar_monto_val(rw.get(c_mod, 0))
                            vk = limpiar_monto_val(rw.get(c_saldo, 0))
                            partida_txt = str(rw.get(c_partida, ""))

                            rows_html_exp += f'<tr><td style="text-align: left; padding-left: 40px;">{partida_txt}</td><td style="text-align: right;">${vg:,.2f}</td><td style="text-align: right;">${vh:,.2f}</td><td style="text-align: right;">${vi:,.2f}</td><td style="text-align: right;">${vj:,.2f}</td><td style="text-align: right;">${vk:,.2f}</td></tr>'

                total_general_devengado += tot_dev_dest

                bloques_ejec_html += f"""
                <div class="bloque-destino">
                    <div class="m-box">
                        <table class="t-hdr">
                            <tr>
                                <td style="width: 25%; text-align: left; font-size: 10px;"><b>Municipalidad de Sunchales</b><br><span style="font-size: 8px; color: #555;">Ejecución de Egresos - Año 2026</span></td>
                                <td style="width: 50%; text-align: center;"><b>REPORTE OFICIAL DE EJECUCIÓN</b><br><small>- Egresos -</small></td>
                                <td style="width: 25%;" class="b-tot"><small>Total Devengado</small><br><b>${tot_dev_dest:,.2f}</b></td>
                            </tr>
                        </table>
                        <div style="border-top: 1px solid #000; font-size: 11px; padding-top: 6px; margin-top: 6px;">
                            <b>SECRETARÍA:</b> {s_exp} | <b>SUBSECRETARÍA:</b> {sub_e} | <span style="float: right;"><b>DESTINO:</b> {str(d_exp).upper()}</span>
                        </div>
                    </div>
                    <table class="tabla-datos">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-left: 8px;">OBJETO / CUENTA / IMPUTACIÓN</th>
                                <th style="text-align: right;">PRESUPUESTO</th>
                                <th style="text-align: right;">DEVENGADO</th>
                                <th style="text-align: right;">EJECUTADO</th>
                                <th style="text-align: right;">MODIFICACIONES</th>
                                <th style="text-align: right;">SALDO</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html_exp}
                        </tbody>
                    </table>
                    <div class="salto-pagina"></div>
                </div>
                """

            html_completo_ejec_oficial = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @page {{ size: A4 landscape; margin: 12mm; }}
                    body {{ font-family: Arial, sans-serif; color: #000; margin: 0 auto; width: 100%; max-width: 1050px; }}
                    .m-box {{ border: 1px solid #000; padding: 10px; margin-bottom: 15px; background-color: #fff; }}
                    .t-hdr {{ width: 100%; border-collapse: collapse; }}
                    .t-hdr td {{ padding: 4px; vertical-align: middle; border: none; }}
                    .b-tot {{ border: 1px solid #000; background-color: #f5f5f5; text-align: center; }}
                    .tabla-datos {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; margin-bottom: 25px; }}
                    .tabla-datos th {{ border-bottom: 2px solid #000; padding: 6px 4px; text-align: center; font-weight: bold; background-color: #f2f2f2; }}
                    .tabla-datos td {{ border-bottom: 1px solid #e0e0e0; padding: 6px 4px; vertical-align: middle; text-align: center; }}
                    .tabla-datos th:first-child, .tabla-datos td:first-child {{ text-align: left !important; padding-left: 8px; }}
                    .salto-pagina {{ page-break-after: always; }}
                    .firmas-container {{ margin-top: 50px; width: 100%; page-break-inside: avoid; }}
                    .firma-box {{ width: 30%; float: left; text-align: center; border-top: 1px solid #000; padding-top: 5px; margin: 0 1.5%; font-size: 11px; font-weight: bold; }}
                    .resumen-final {{ border: 2px solid #000; padding: 15px; margin-top: 20px; background-color: #fafafa; text-align: center; font-size: 14px; page-break-inside: avoid; }}
                </style>
            </head>
            <body onload="window.print();">
                {bloques_ejec_html}
                <div class="resumen-final">
                    <b>TOTAL GENERAL DEVENGADO MUNICIPAL:</b> ${total_general_devengado:,.2f}
                </div>
                <div class="firmas-container">
                    <div class="firma-box">Responsable Presupuesto</div>
                    <div class="firma-box">Sec. Hacienda</div>
                    <div class="firma-box">Intendente</div>
                </div>
            </body>
            </html>
            """

            st.download_button(
                label="📥 Descargar Reporte Oficial Consolidado (HTML/PDF)",
                data=html_completo_ejec_oficial,
                file_name=f"Reporte_Ejecucion_Consolidado_{time.strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
                type="primary"
            )

        # -------------------------------------------------------------
        # SOLAPA 6: REPORTE POR FINALIDAD Y FUNCIÓN (CON IMPRESIÓN)
        # -------------------------------------------------------------
        with tab_ejec_6:
            st.markdown("##### 🏛️ Reporte Consolidado por Finalidad y Función")
            st.info("💡 Este reporte agrupa la ejecución de egresos según la finalidad y función presupuestaria, con opción de descarga e impresión formal.")

            if not df_validas.empty and "FINALIDAD" in [c.upper() for c in df_validas.columns] or any("FINALIDAD" in c for c in df_validas.columns):
                col_fin_detectada = [c for c in df_validas.columns if "FINALIDAD" in c.upper()][0]

                df_validas["_DEV_NUM"] = df_validas[c_dev].apply(limpiar_monto_val)
                df_validas["_PRES_NUM"] = df_validas[c_pres].apply(limpiar_monto_val)
                df_validas["_EJEC_NUM"] = df_validas[c_ejec].apply(limpiar_monto_val)
                df_validas["_MOD_NUM"] = df_validas[c_mod].apply(limpiar_monto_val)
                df_validas["_SALDO_NUM"] = df_validas[c_saldo].apply(limpiar_monto_val)

                df_fin_res = df_validas.groupby(col_fin_detectada).agg({
                    "_PRES_NUM": "sum",
                    "_DEV_NUM": "sum",
                    "_EJEC_NUM": "sum",
                    "_MOD_NUM": "sum",
                    "_SALDO_NUM": "sum"
                }).reset_index()

                df_fin_res.columns = ["FINALIDAD / FUNCIÓN", "PRESUPUESTO", "DEVENGADO", "EJECUTADO", "MODIFICACIONES", "SALDO"]

                df_fin_vista = df_fin_res.copy()
                for c_m in ["PRESUPUESTO", "DEVENGADO", "EJECUTADO", "MODIFICACIONES", "SALDO"]:
                    df_fin_vista[c_m] = df_fin_vista[c_m].map(lambda x: f"${x:,.2f}")

                st.dataframe(df_fin_vista, use_container_width=True, hide_index=True)

                tot_gral_fin = df_fin_res["DEVENGADO"].sum()
                rows_fin_html = ""
                for _, r_f in df_fin_res.iterrows():
                    rows_fin_html += f"""
                    <tr>
                        <td style="text-align: left; padding-left: 8px; font-weight: bold;">{r_f['FINALIDAD / FUNCIÓN']}</td>
                        <td style="text-align: right;">${r_f['PRESUPUESTO']:,.2f}</td>
                        <td style="text-align: right;">${r_f['DEVENGADO']:,.2f}</td>
                        <td style="text-align: right;">${r_f['EJECUTADO']:,.2f}</td>
                        <td style="text-align: right;">${r_f['MODIFICACIONES']:,.2f}</td>
                        <td style="text-align: right;">${r_f['SALDO']:,.2f}</td>
                    </tr>
                    """

                html_reporte_fin = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @page {{ size: A4 landscape; margin: 12mm; }}
                        body {{ font-family: Arial, sans-serif; color: #000; margin: 0 auto; width: 100%; max-width: 1050px; }}
                        .m-box {{ border: 1px solid #000; padding: 10px; margin-bottom: 15px; background-color: #fff; }}
                        .t-hdr {{ width: 100%; border-collapse: collapse; }}
                        .t-hdr td {{ padding: 4px; vertical-align: middle; border: none; }}
                        .b-tot {{ border: 1px solid #000; background-color: #f5f5f5; text-align: center; }}
                        .tabla-datos {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; margin-bottom: 25px; }}
                        .tabla-datos th {{ border-bottom: 2px solid #000; padding: 6px 4px; font-weight: bold; background-color: #f2f2f2; }}
                        .tabla-datos td {{ border-bottom: 1px solid #e0e0e0; padding: 6px 4px; vertical-align: middle; }}
                        .resumen-final {{ border: 2px solid #000; padding: 15px; margin-top: 20px; background-color: #fafafa; text-align: center; font-size: 14px; page-break-inside: avoid; }}
                        .firmas-container {{ margin-top: 50px; width: 100%; page-break-inside: avoid; }}
                        .firma-box {{ width: 30%; float: left; text-align: center; border-top: 1px solid #000; padding-top: 5px; margin: 0 1.5%; font-size: 11px; font-weight: bold; }}
                    </style>
                </head>
                <body onload="window.print();">
                    <div class="m-box">
                        <table class="t-hdr">
                            <tr>
                                <td style="width: 25%; text-align: left; font-size: 10px;"><b>Municipalidad de Sunchales</b><br><span style="font-size: 8px; color: #555;">Ejecución de Egresos - Año 2026</span></td>
                                <td style="width: 50%; text-align: center;"><b>REPORTE OFICIAL POR FINALIDAD Y FUNCIÓN</b><br><small>- Control Financiero -</small></td>
                                <td style="width: 25%;" class="b-tot"><small>Total Devengado</small><br><b>${tot_gral_fin:,.2f}</b></td>
                            </tr>
                        </table>
                    </div>
                    <table class="tabla-datos">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-left: 8px;">FINALIDAD / FUNCIÓN</th>
                                <th style="text-align: right;">PRESUPUESTO</th>
                                <th style="text-align: right;">DEVENGADO</th>
                                <th style="text-align: right;">EJECUTADO</th>
                                <th style="text-align: right;">MODIFICACIONES</th>
                                <th style="text-align: right;">SALDO</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_fin_html}
                        </tbody>
                    </table>
                    <div class="resumen-final">
                        <b>TOTAL GENERAL DEVENGADO MUNICIPAL:</b> ${tot_gral_fin:,.2f}
                    </div>
                    <div class="firmas-container">
                        <div class="firma-box">Responsable Presupuesto</div>
                        <div class="firma-box">Sec. Hacienda</div>
                        <div class="firma-box">Intendente</div>
                    </div>
                </body>
                </html>
                """

                st.download_button(
                    label="📥 Descargar Reporte Oficial por Finalidad (PDF/HTML)",
                    data=html_reporte_fin,
                    file_name=f"Reporte_Finalidad_Funcion_{time.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ No se encontró la columna de finalidad en la planilla.")
