from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert('/home/ubuntu/upload/03.2024-EXTRATOBBPDF.pdf')

print(result.document.export_to_markdown())

