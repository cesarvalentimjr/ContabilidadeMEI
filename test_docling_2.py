from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("/home/ubuntu/upload/IntEr-netBank_Ing----CAIXa.pdf-JUNHO.pdf")

print(result.document.export_to_markdown())

