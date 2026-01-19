"""Geração de arquivos CSV para anexos de email."""
import csv
import io
from datetime import date
from search.source import Report


def generate_csv_from_report(report: Report) -> bytes:
    """
    Gera um arquivo CSV a partir de um relatório de busca.
    
    O CSV contém as seguintes colunas:
    - Data Publicação: Data do diário oficial
    - Termo: Termo que foi buscado
    - Página: Número da página onde foi encontrado
    - Conteúdo: Trecho do conteúdo onde o termo foi encontrado
    - Link: URL direta para a página do diário
    
    Args:
        report: Relatório de busca com highlights e termos
        
    Returns:
        Conteúdo do CSV em bytes (UTF-8 com BOM para Excel)
    """
    output = io.StringIO()
    
    # Adicionar BOM UTF-8 para compatibilidade com Excel
    output.write('\ufeff')
    
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Cabeçalho
    writer.writerow([
        'Data Publicação',
        'Termo',
        'Página',
        'Conteúdo',
        'Link'
    ])
    
    # Data formatada
    date_str = report.publish_date.strftime('%d/%m/%Y')
    
    # Escrever cada highlight
    for highlight in report.highlights:
        # Limpar conteúdo (remover tags HTML se houver)
        content = highlight.content.replace('<b>', '').replace('</b>', '').strip()
        
        writer.writerow([
            date_str,
            highlight.term,
            highlight.page,
            content,
            highlight.page_url
        ])
    
    # Converter para bytes (UTF-8)
    csv_content = output.getvalue()
    return csv_content.encode('utf-8-sig')


def get_csv_filename(report: Report) -> str:
    """
    Gera nome de arquivo CSV baseado na data do relatório.
    
    Args:
        report: Relatório de busca
        
    Returns:
        Nome do arquivo CSV (ex: notificacoes_2026-01-14.csv)
    """
    date_str = report.publish_date.strftime('%Y-%m-%d')
    return f"notificacoes_{date_str}.csv"
