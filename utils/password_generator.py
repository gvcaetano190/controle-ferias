"""
Gerador de senhas seguras.

Fornece funcionalidades para gerar senhas fortes automaticamente
com opções de personalização.
"""

import random
import string
from typing import Dict, Optional


class PasswordGenerator:
    """Gerador de senhas seguras com opções customizáveis."""

    # Conjuntos de caracteres
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(self):
        """Inicializa o gerador."""
        pass

    def gerar_senha_forte(self, length: int = 12,
                         include_lowercase: bool = True,
                         include_uppercase: bool = True,
                         include_digits: bool = True,
                         include_symbols: bool = True,
                         exclude_similar: bool = False) -> str:
        """
        Gera uma senha forte com as características especificadas.

        Args:
            length: Comprimento da senha (mínimo 8)
            include_lowercase: Incluir letras minúsculas
            include_uppercase: Incluir letras maiúsculas
            include_digits: Incluir números
            include_symbols: Incluir símbolos especiais
            exclude_similar: Excluir caracteres similares (0, O, I, l, etc.)

        Returns:
            Senha gerada
        """
        if length < 8:
            length = 8

        # Define conjunto de caracteres base
        chars = ""
        if include_lowercase:
            chars += self.LOWERCASE
        if include_uppercase:
            chars += self.UPPERCASE
        if include_digits:
            chars += self.DIGITS
        if include_symbols:
            chars += self.SYMBOLS

        if not chars:
            raise ValueError("Pelo menos um tipo de caractere deve ser selecionado.")

        # Remove caracteres similares se solicitado
        if exclude_similar:
            chars = chars.translate(str.maketrans('', '', '0OIl1'))

        # Garante que pelo menos um de cada tipo seja incluído
        password = []

        # Adiciona pelo menos um de cada tipo obrigatório
        if include_lowercase:
            password.append(random.choice(self.LOWERCASE))
        if include_uppercase:
            password.append(random.choice(self.UPPERCASE))
        if include_digits:
            password.append(random.choice(self.DIGITS))
        if include_symbols:
            password.append(random.choice(self.SYMBOLS))

        # Preenche o resto da senha
        remaining_length = length - len(password)
        password.extend(random.choices(chars, k=remaining_length))

        # Embaralha a senha
        random.shuffle(password)

        return ''.join(password)

    def avaliar_forca_senha(self, senha: str) -> Dict[str, any]:
        """
        Avalia a força de uma senha.

        Args:
            senha: Senha a ser avaliada

        Returns:
            Dict com score, força e sugestões
        """
        score = 0
        issues = []

        # Comprimento
        if len(senha) < 8:
            issues.append("Mínimo 8 caracteres")
            score += 0
        elif len(senha) >= 12:
            score += 2
        else:
            score += 1

        # Letra minúscula
        if not any(c.islower() for c in senha):
            issues.append("Pelo menos 1 letra minúscula")
        else:
            score += 1

        # Letra maiúscula
        if not any(c.isupper() for c in senha):
            issues.append("Pelo menos 1 letra maiúscula")
        else:
            score += 1

        # Número
        if not any(c.isdigit() for c in senha):
            issues.append("Pelo menos 1 número")
        else:
            score += 1

        # Caractere especial
        if not any(c in self.SYMBOLS for c in senha):
            issues.append("Pelo menos 1 caractere especial")
        else:
            score += 1

        # Variedade
        char_types = 0
        if any(c.islower() for c in senha): char_types += 1
        if any(c.isupper() for c in senha): char_types += 1
        if any(c.isdigit() for c in senha): char_types += 1
        if any(c in self.SYMBOLS for c in senha): char_types += 1

        if char_types >= 3:
            score += 1

        # Define nível de força
        if score <= 2:
            forca = "Muito Fraca"
            cor = "🔴"
        elif score <= 4:
            forca = "Fraca"
            cor = "🟠"
        elif score <= 6:
            forca = "Média"
            cor = "🟡"
        elif score <= 8:
            forca = "Forte"
            cor = "🟢"
        else:
            forca = "Muito Forte"
            cor = "🔵"

        return {
            "score": score,
            "max_score": 9,
            "forca": forca,
            "cor": cor,
            "issues": issues,
            "sugestoes": self._gerar_sugestoes(issues)
        }

    def _gerar_sugestoes(self, issues: list) -> list:
        """Gera sugestões baseadas nos problemas encontrados."""
        sugestoes = []

        for issue in issues:
            if "8 caracteres" in issue:
                sugestoes.append("Use pelo menos 8 caracteres")
            elif "minúscula" in issue:
                sugestoes.append("Inclua letras minúsculas (a-z)")
            elif "maiúscula" in issue:
                sugestoes.append("Inclua letras maiúsculas (A-Z)")
            elif "número" in issue:
                sugestoes.append("Inclua números (0-9)")
            elif "especial" in issue:
                sugestoes.append("Inclua caracteres especiais (!@#$%^&*)")

        return sugestoes

    def fortalecer_palavra(self, palavra: str, adicionar_numeros: bool = True, 
                          adicionar_simbolos: bool = True) -> str:
        """
        Transforma uma palavra simples em uma senha forte.
        
        Args:
            palavra: Palavra base (ex: "gabriel")
            adicionar_numeros: Adicionar números à senha
            adicionar_simbolos: Adicionar símbolos à senha
            
        Returns:
            Senha fortalecida (ex: "Gabriel123!@#")
        """
        if not palavra:
            return ""
        
        # Remove espaços e converte para minúsculas
        palavra = palavra.strip().lower()
        
        # Transforma a palavra: primeira letra maiúscula, alterna maiúsculas/minúsculas
        palavra_fortalecida = ""
        for i, char in enumerate(palavra):
            if char.isalpha():
                # Primeira letra sempre maiúscula, depois alterna
                if i == 0:
                    palavra_fortalecida += char.upper()
                elif i % 2 == 0:
                    palavra_fortalecida += char.upper()
                else:
                    palavra_fortalecida += char.lower()
            else:
                palavra_fortalecida += char
        
        # Adiciona números se solicitado
        if adicionar_numeros:
            # Adiciona números aleatórios (2-3 dígitos)
            numeros = ''.join(random.choices(self.DIGITS, k=random.randint(2, 3)))
            palavra_fortalecida += numeros
        
        # Adiciona símbolos se solicitado
        if adicionar_simbolos:
            # Adiciona símbolos aleatórios (1-2 símbolos)
            simbolos = ''.join(random.choices(self.SYMBOLS, k=random.randint(1, 2)))
            palavra_fortalecida += simbolos
        
        return palavra_fortalecida

    def gerar_templates(self) -> Dict[str, str]:
        """
        Gera exemplos de senhas para diferentes propósitos.

        Returns:
            Dict com templates de senha
        """
        return {
            "básica": self.gerar_senha_forte(8, True, True, False),
            "segura": self.gerar_senha_forte(12, True, True, True),
            "muito_segura": self.gerar_senha_forte(16, True, True, True),
            "wifi": self.gerar_senha_forte(10, True, True, True),
            "banco": self.gerar_senha_forte(20, True, True, True)
        }


# Instância global
password_generator = PasswordGenerator()





