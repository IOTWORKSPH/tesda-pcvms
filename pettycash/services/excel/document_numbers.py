def preliminary_document_number(doc_type, document_date):
    return f"{doc_type}-{document_date.strftime('%Y-%m')}-_________"
