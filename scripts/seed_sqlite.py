#!/usr/bin/env python3
"""
Seed script for CourseSphere SQLite Database.
Creates and populates:
- courses table (id, name, section_id, semester, department, instructor)
- course_descriptions table (id, course_id, description)
- reddit_posts and reddit_comments tables

Handles both 'cornell-course-sphere-data' and typo 'cournell-course-sphere-data' paths
to ensure seamless local testing and backward compatibility with db.py.
"""

import sqlite3
import os
import sys

# Paths to populate
DB_PATHS = [
    os.path.join("backend", "cornell-course-sphere-data", "roster_reviews.sqlite.db"),
    os.path.join("cournell-course-sphere-data", "roster_reviews.sqlite.db"),
    os.path.join("backend", "cournell-course-sphere-data", "roster_reviews.sqlite.db")
]

COURSES_DATA = [
    (1, "CS 4820: Introduction to Analysis of Algorithms", 101, "FA24", "CS", "Eva Tardos"),
    (2, "CS 4410: Operating Systems", 101, "FA24", "CS", "Lorenzo Alvisi"),
    (3, "CS 5430: System Security", 102, "SP24", "CS", "Fred B. Schneider"),
    (4, "CS 5412: Cloud Computing", 101, "SP24", "CS", "Ken Birman"),
    (5, "CS 2110: Object-Oriented Programming and Data Structures", 201, "FA24", "CS", "David Gries"),
    (6, "INFO 2950: Mathematical Foundations for Data Science", 101, "FA24", "INFO", "Paul Ginsparg"),
    (7, "INFO 1300: Introductory Design and Programming for the Web", 101, "SP24", "INFO", "Kyle Harms"),
    (8, "MATH 4710: Basic Probability", 101, "FA24", "MATH", "Laurent Saloff-Coste"),
    (9, "ECE 4750: Computer Architecture", 101, "FA24", "ECE", "Christopher Batten"),
    (10, "CS 4700: Foundations of Artificial Intelligence", 101, "SP24", "CS", "Bart Selman")
]

DESCRIPTIONS_DATA = [
    (1, 1, "Desenvolvimento e análise de algoritmos eficientes: programação dinâmica, grafos, fluxo em redes, complexidade computacional e problemas NP-completos."),
    (2, 2, "Fundamentos de sistemas operacionais: concorrência, processos, threads, sincronização, memória virtual, sistemas de arquivos e tolerância a falhas."),
    (3, 3, "Princípios de segurança em sistemas computacionais: confidencialidade, integridade, disponibilidade, autenticação, controle de acesso e criptografia aplicada."),
    (4, 4, "Arquitetura e operação de nuvens distribuídas: escalabilidade, consistência eventual, orquestração e confiabilidade (SRE) em larga escala."),
    (5, 5, "Paradigma orientado a objetos, estruturas de dados fundamentais (árvores, tabelas hash), recursão e correção de programas em Java."),
    (6, 6, "Métodos estatísticos e matemáticos fundamentais para ciência de dados, regressão, probabilidade e inferência exploratória."),
    (7, 7, "Desenvolvimento front-end web moderno, design responsivo, usabilidade e integração de dados estruturados."),
    (8, 8, "Cálculo de probabilidades, variáveis aleatórias discretas e contínuas, distribuições conjuntas e lei dos grandes números."),
    (9, 9, "Microarquitetura de processadores, hierarquia de cache, pipelining, superescalaridade e suporte de hardware a sistemas operacionais."),
    (10, 10, "Busca heurística, modelos probabilísticos, lógica de primeira ordem, planejamento automatizado e introdução a aprendizado de máquina.")
]

REDDIT_POSTS_DATA = [
    (1, "Cornell", "Dicas para sobreviver a CS 4820 (Algo)?", "https://reddit.com/r/Cornell/algo", "algo_student", 42, 15, 1720000000, "Alguém tem recomendações sobre os problem sets de Algoritmos?", "/r/Cornell/comments/1/algo"),
    (2, "Cornell", "CS 5430 (Security) vale a pena?", "https://reddit.com/r/Cornell/sec", "sec_enthusiast", 58, 8, 1720100000, "Excelente disciplina, aborda a base teórica e prática de segurança e confiabilidade.", "/r/Cornell/comments/2/sec")
]

REDDIT_COMMENTS_DATA = [
    (1, 1, "Cornell", "ta_algo", "user_10", "1", 25, 1720001000, "Comece os problem sets no primeiro dia e use os office hours!", "/r/Cornell/comments/1/algo/c1"),
    (2, 2, "Cornell", "infosec_fan", "user_20", "2", 18, 1720102000, "Altamente recomendado para quem quer seguir carreira em AppSec e infraestrutura.", "/r/Cornell/comments/2/sec/c2")
]

def seed_database(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[*] Populando banco SQLite em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        section_id INTEGER,
        semester TEXT,
        department TEXT,
        instructor TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS course_descriptions (
        id INTEGER PRIMARY KEY,
        course_id INTEGER,
        description TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reddit_posts (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subreddit TEXT,
        title TEXT,
        url TEXT,
        author TEXT,
        score INTEGER,
        num_comments INTEGER,
        created_utc INTEGER,
        selftext TEXT,
        permalink TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reddit_comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        subreddit TEXT,
        username TEXT,
        user_id TEXT,
        parent_id TEXT,
        score INTEGER,
        created_utc INTEGER,
        body TEXT,
        permalink TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES reddit_posts(post_id)
    );
    """)
    
    # Insert or replace course records
    cursor.executemany("""
    INSERT OR REPLACE INTO courses (id, name, section_id, semester, department, instructor)
    VALUES (?, ?, ?, ?, ?, ?);
    """, COURSES_DATA)
    
    cursor.executemany("""
    INSERT OR REPLACE INTO course_descriptions (id, course_id, description)
    VALUES (?, ?, ?);
    """, DESCRIPTIONS_DATA)
    
    cursor.executemany("""
    INSERT OR REPLACE INTO reddit_posts (post_id, subreddit, title, url, author, score, num_comments, created_utc, selftext, permalink)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, REDDIT_POSTS_DATA)
    
    cursor.executemany("""
    INSERT OR REPLACE INTO reddit_comments (comment_id, post_id, subreddit, username, user_id, parent_id, score, created_utc, body, permalink)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, REDDIT_COMMENTS_DATA)
    
    conn.commit()
    
    # Verify count
    cursor.execute("SELECT COUNT(*) FROM courses;")
    total_courses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM course_descriptions;")
    total_desc = cursor.fetchone()[0]
    
    conn.close()
    print(f"[+] Sucesso: {total_courses} cursos e {total_desc} descrições inseridos em {db_path}")

def main():
    print("=" * 60)
    print(" CourseSphere — Seed do Banco de Dados SQLite")
    print("=" * 60)
    
    for path in DB_PATHS:
        try:
            seed_database(path)
        except Exception as e:
            print(f"[-] Erro ao popular {path}: {e}")
            
    print("\n[+] Seed do banco SQLite concluído com sucesso!")

if __name__ == "__main__":
    main()

