

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from langchain_openai import ChatOpenAI

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )



class EstadoJogo:
 
    def __init__(self):
        self.historia: str = ""
        self.solucao: dict = {}
        self.alibis: dict = {}
        self.personagens: list = [] 
        self.historico: list = []
        self.tentativas: int = 0
        self.max_tentativas: int = 5
        self.game_over: bool = False
        self.vitoria: bool = False
        self.armas: list = []
        self.locais: list = []

    def to_dict(self) -> dict:
        return {
            "historia":       self.historia,
            "solucao":        self.solucao,
            "alibis":         self.alibis,
            "personagens":    self.personagens,
            "historico":      self.historico,
            "tentativas":     self.tentativas,
            "max_tentativas": self.max_tentativas,
            "game_over":      self.game_over,
            "vitoria":        self.vitoria,
            "armas":          self.armas,
            "locais":         self.locais,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EstadoJogo":
        obj = cls()
        obj.historia       = data.get("historia", "")
        obj.solucao        = data.get("solucao", {})
        obj.alibis         = data.get("alibis", {})
        obj.personagens    = data.get("personagens", [])
        obj.historico      = data.get("historico", [])
        obj.tentativas     = data.get("tentativas", 0)
        obj.max_tentativas = data.get("max_tentativas", 5)
        obj.game_over      = data.get("game_over", False)
        obj.vitoria        = data.get("vitoria", False)
        obj.armas          = data.get("armas", [])
        obj.locais         = data.get("locais", [])
        return obj

    def get_personagem(self, pid: str) -> dict | None:
        """Busca personagem pelo id (p1, p2, p3)."""
        return next((p for p in self.personagens if p["id"] == pid), None)

    def get_arma(self, pid: str) -> dict | None:
        """Busca arma pelo id (a1, a2, a3)."""
        return next((p for p in self.armas if p["id"] == pid), None)

    def get_local(self, pid: str) -> dict | None:
        """Busca local pelo id (l1, l2, l3)."""
        return next((p for p in self.locais if p["id"] == pid), None)

    def registrar_interrogatorio(self, personagem: str, pergunta: str, resposta: str):
        self.historico.append({
            "personagem": personagem,
            "pergunta":   pergunta,
            "resposta":   resposta,
        })

    def resumo_historico(self) -> str:
        if not self.historico:
            return "Nenhum interrogatório realizado ainda."
        return "\n".join(
            f"[{e.get('nome', e.get('personagem','?')).upper()}] P: {e['pergunta']} | R: {e['resposta']}"
            for e in self.historico
        )

    @property
    def tentativas_restantes(self) -> int:
        return self.max_tentativas - self.tentativas
    
# ==============================
# AGENTE 1 — Narrador / Criador da História
# ==============================

_story_prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é o narrador de um jogo de mistério de assassinato no estilo Murdle.
     
Gere UM mistério curto, atmosférico e logicamente consistente por execução.

O cenário NÃO está limitado a mansões — pode ser qualquer ambiente realista.

Regras de construção:
Crie exatamente 3 personagens únicos, com:
nome inventado
papel coerente com o ambiente
gênero ("m" ou "f")

Crie:
3 armas possíveis
3 locais possíveis dentro do mesmo cenário

REGRA DE COERÊNCIA CRÍTICA (OBRIGATÓRIA):
Tudo deve ser coerente entre si e plausível.

Lógica do mistério:
Escolha secretamente:
1 culpado
1 arma usada
1 local do crime

NÃO revele explicitamente quem é o culpado.

História:
Escreva 2 parágrafos atmosféricos com pistas sutis.

Álibis:
Cada personagem deve ter um álibi curto, plausível e com brecha.

Saída:
Responda APENAS com JSON válido.

Formato JSON:

{{
"historia": "2 parágrafos atmosféricos",
"personagens": [
{{"id": "p1", "nome": "Nome Inventado", "papel": "papel no cenário", "genero": "m"}},
{{"id": "p2", "nome": "Nome Inventado", "papel": "papel no cenário", "genero": "f"}},
{{"id": "p3", "nome": "Nome Inventado", "papel": "papel no cenário", "genero": "m"}}
],
"culpado_id": "p1",

"armas": [
{{"id": "a1", "nome": "Nome da arma"}},
{{"id": "a2", "nome": "Nome da arma"}},
{{"id": "a3", "nome": "Nome da arma"}}
],
"arma_usada_id": "a1",

"locais": [
{{"id": "l1", "nome": "Nome do local"}},
{{"id": "l2", "nome": "Nome do local"}},
{{"id": "l3", "nome": "Nome do local"}}
],
"local_crime_id": "l1",

"alibis": {{
"p1": "alibi curto",
"p2": "alibi curto",
"p3": "alibi curto"
}}
}}"""),
    ("human", "Gere o mistério agora."),
])


def criar_historia(state: EstadoJogo) -> None:
    llm = get_llm()
    chain = _story_prompt | llm
    resposta = chain.invoke({})
    conteudo = resposta.content.strip()
    if conteudo.startswith("```"):
        conteudo = conteudo.split("```")[1]
        if conteudo.startswith("json"):
            conteudo = conteudo[4:]

    data = json.loads(conteudo)

    state.historia    = data["historia"]
    state.personagens = data["personagens"]
    state.armas =       data["armas"]    
    state.locais =      data["locais"]   

    culpado = state.get_personagem(data["culpado_id"])
    arma = state.get_arma(data["arma_usada_id"])
    local = state.get_local(data["local_crime_id"])
    
    state.solucao = {
        "pessoa_id": data["culpado_id"],
        "pessoa":    culpado["nome"],
        "arma":      arma["nome"],
        "local":     local["nome"],
    }
    state.alibis = data.get("alibis", {})  


# ==============================
# AGENTE 2 — Suspeito
# ==============================

_suspect_prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é {personagem} em um jogo de detetive de assassinato.

História do crime:
{historia}

Seu álibi (só você sabe — use para se defender):
{alibi}

Você é o culpado? {e_culpado}

Histórico de interrogatórios desta sessão:
{historico}

Regras:
Se for culpado escolha uma estratégia:

1) negar diretamente
2) mudar de assunto
3) insinuar suspeita sobre outro
4) responder parcialmente
- Se NÃO for culpado: responda honestamente, mas pode ter pequenos segredos.
- Nunca quebre o personagem.
- 2 a 4 frases curtas, estilo noir dramático, primeira pessoa."""),
    ("human", "Pergunta do detetive: {pergunta}"),
])


def interrogar_suspeito(pid: str, pergunta: str, state: EstadoJogo) -> str:
    personagem = state.get_personagem(pid)
    if not personagem:
        raise ValueError(f"Personagem {pid} não encontrado")

    llm = get_llm()
    chain = _suspect_prompt | llm

    e_culpado = "SIM" if pid == state.solucao.get("pessoa_id") else "NÃO"
    alibi     = state.alibis.get(pid, "Sem álibi registrado.")

    resposta = chain.invoke({
        "personagem": f"{personagem['nome']} ({personagem['papel']})",
        "historia":   state.historia,
        "alibi":      alibi,
        "e_culpado":  e_culpado,
        "historico":  state.resumo_historico(),
        "pergunta":   pergunta,
    })

    state.historico.append({
        "pid": pid,
        "nome": personagem["nome"],
        "pergunta": pergunta,
        "resposta": resposta.content,
    })
    return resposta.content


# ==============================
# AGENTE 3 — / Gerador de Dicas
# ==============================

_hint_prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é um investigador sênior guiando um detetive novato.
Conhece a solução real. Oriente sem revelar diretamente.

Regras:
1. NUNCA revele a resposta diretamente.
2. Se o jogador acertou algum campo, confirme isso.
3. Baseie a dica no histórico de interrogatórios quando possível.
4. Com 1 ou 2 tentativas restantes, seja mais específico (mas não entregue).
5. Seja dramático — veterano endurecido.
6. 2 a 3 frases."""),
    ("human", """Solução real:
- Culpado: {pessoa}
- Arma:    {arma}
- Local:   {local}

Tentativa do jogador:
- Culpado: {pessoa_user} ({resultado_pessoa})
- Arma:    {arma_user} ({resultado_arma})
- Local:   {local_user} ({resultado_local})

Tentativa {tentativa_num} de {max_tentativas} (restam {restantes}).

Histórico de interrogatórios:
{historico}

Gere a dica."""),
])


def gerar_dica(tentativa: dict, erros: list, acertos: list, state: EstadoJogo) -> str:
    """Chama o Agente 3 e retorna a dica contextual."""
    llm = get_llm()
    chain = _hint_prompt | llm

    resposta = chain.invoke({
        "pessoa":          state.solucao["pessoa"],
        "arma":            state.solucao["arma"],
        "local":           state.solucao["local"],
        "pessoa_user":     tentativa["pessoa"],
        "arma_user":       tentativa["arma"],
        "local_user":      tentativa["local"],
        "resultado_pessoa": "CORRETO" if "pessoa" in acertos else "ERRADO",
        "resultado_arma":   "CORRETO" if "arma"   in acertos else "ERRADO",
        "resultado_local":  "CORRETO" if "local"  in acertos else "ERRADO",
        "tentativa_num":   state.tentativas,
        "max_tentativas":  state.max_tentativas,
        "restantes":       state.tentativas_restantes,
        "historico":       state.resumo_historico(),
    })

    return resposta.content


# ==============================
# REGRA DE DECISÃO
# ==============================

def verificar_tentativa(solucao: dict, tentativa: dict) -> tuple[str, list, list]:
    """
    Compara tentativa com solução de forma normalizada.
    Retorna: (resultado, erros, acertos)
    """
    erros   = []
    acertos = []

    for campo in ["pessoa", "arma", "local"]:
        if tentativa[campo].strip().lower() == solucao[campo].strip().lower():
            acertos.append(campo)
        else:
            erros.append(campo)

    return ("acertou" if not erros else "errou"), erros, acertos
