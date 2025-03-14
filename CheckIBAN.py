import streamlit as st
import pandas as pd
import re
from io import BytesIO

def iban_to_numeric(iban):
    """Zet een IBAN om naar een numerieke string voor validatie."""
    iban = iban.replace(" ", "").replace("-", "").replace(".", "")  # Verwijder spaties, streepjes, punten
    if not iban.startswith("BE") or len(iban) != 16:
        return None
    iban_rearranged = iban[4:] + iban[:4]  # Verplaats landcode en checksum naar achteren
    numeric_iban = "".join(str(ord(c) - 55) if c.isalpha() else c for c in iban_rearranged)
    return int(numeric_iban)

def is_valid_iban(iban):
    """Controleert of een IBAN geldig is."""
    numeric_iban = iban_to_numeric(iban)
    if numeric_iban is None:
        return False
    return numeric_iban % 97 == 1

def process_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    
    # Zoek de kolom met Belgische IBAN's
    account_col = None
    for col in df.columns:
        if df[col].astype(str).str.match(r'(BE\d{2}[-. ]?\d{4}[-. ]?\d{4}[-. ]?\d{4})').any():
            account_col = col
            break
    
    if account_col is None:
        return None, "Geen kolom met Belgische IBAN's gevonden."
    
    # Filter geldige IBAN's
    df['valid'] = df[account_col].astype(str).apply(is_valid_iban)
    valid_df = df[df['valid']].drop(columns=['valid'])
    invalid_count = len(df) - len(valid_df)
    
    # Opslaan als BytesIO voor download
    output = BytesIO()
    valid_df.to_excel(output, index=False, engine='xlsxwriter')
    output.seek(0)
    
    return output, f"{len(df)} rijen gecontroleerd: {invalid_count} ongeldige nummers verwijderd, {len(valid_df)} rijen over."

# Streamlit UI
st.title("Belgische IBAN Validator")
uploaded_file = st.file_uploader("Upload een Excel-bestand", type=["xls", "xlsx"])

if uploaded_file is not None:
    cleaned_file, message = process_file(uploaded_file)
    st.write(message)
    
    if cleaned_file:
        cleaned_filename = uploaded_file.name.replace('.xlsx', '_cleaned.xlsx')
        st.download_button(label="Download opgeschoond bestand", data=cleaned_file, file_name=cleaned_filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
