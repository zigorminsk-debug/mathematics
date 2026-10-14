package by.ziv.ctmaths

import java.util.Locale
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.asin
import kotlin.math.atan
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.floor
import kotlin.math.ln
import kotlin.math.log10
import kotlin.math.pow
import kotlin.math.round
import kotlin.math.sign
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan
import org.json.JSONArray
import org.json.JSONObject


/* -------------------------------------------------------------------------- */
private val CONSTANTS = mapOf("pi" to PI, "e" to Math.E, "tau" to 2 * PI)

private val FUNCTIONS: Map<String, (Double) -> Double> = mapOf(
        "sin" to { x -> sin(x) },
        "cos" to { x -> cos(x) },
        "tan" to { x -> tan(x) },
        "tg" to { x -> tan(x) },
        "ctg" to { x -> 1.0 / tan(x) },
        "cot" to { x -> 1.0 / tan(x) },
        "asin" to { x -> asin(x) },
        "acos" to { x -> acos(x) },
        "atan" to { x -> atan(x) },
        "arcsin" to { x -> asin(x) },
        "arccos" to { x -> acos(x) },
        "arctg" to { x -> atan(x) },
        "arctan" to { x -> atan(x) },
        "sqrt" to { x -> sqrt(x) },
        "abs" to { x -> abs(x) },
        "ln" to { x -> ln(x) },
        "lg" to { x -> log10(x) },
        "log" to { x -> log10(x) },
        "exp" to { x -> exp(x) },
        "round" to { x -> round(x) },
        "floor" to { x -> floor(x) },
        "ceil" to { x -> ceil(x) },
        "sign" to { x -> sign(x) },
    )

/*  Разбор простых выражений (та же грамматика, что в JS и Python)            */
/* -------------------------------------------------------------------------- */

private enum class TokenType { NUMBER, NAME, OPERATOR }

private data class ExpressionToken(val type: TokenType, val text: String, val number: Double = 0.0)

private sealed class ExpressionNode {
    data class Number(val value: Double) : ExpressionNode()
    data class Unary(val operator: String, val operand: ExpressionNode) : ExpressionNode()
    data class Binary(val operator: String, val left: ExpressionNode, val right: ExpressionNode) : ExpressionNode()
    data class Function(val name: String, val argument: ExpressionNode) : ExpressionNode()
}

/** Recursive-descent parser: + - * / % ^, parentheses, functions, constants. */
private class ExpressionParser(private val tokens: List<ExpressionToken>) {

    private var position = 0

    fun parse(): ExpressionNode {
        val tree = expression()
        if (position != tokens.size) throw IllegalArgumentException("trailing input")
        return tree
    }

    private fun peek(): ExpressionToken? = if (position < tokens.size) tokens[position] else null

    private fun take(): ExpressionToken? = if (position < tokens.size) tokens[position++] else null

    private fun isOperator(token: ExpressionToken?, value: String): Boolean =
        token != null && token.type == TokenType.OPERATOR && token.text == value

    private fun startsAtom(token: ExpressionToken?): Boolean = when {
        token == null -> false
        token.type == TokenType.NUMBER || token.type == TokenType.NAME -> true
        else -> isOperator(token, "(")
    }

    private fun expression(): ExpressionNode {
        var node = term()
        while (isOperator(peek(), "+") || isOperator(peek(), "-")) {
            val operator = take()!!.text
            node = ExpressionNode.Binary(operator, node, term())
        }
        return node
    }

    private fun term(): ExpressionNode {
        var node = unary()
        while (true) {
            val token = peek()
            if (isOperator(token, "*") || isOperator(token, "/") || isOperator(token, "%")) {
                val operator = take()!!.text
                node = ExpressionNode.Binary(operator, node, unary())
                continue
            }
            // неявное умножение: «6√2» — это 6·√2, «2π» — это 2·π, «3(4+1)»
            if (startsAtom(token)) {
                node = ExpressionNode.Binary("*", node, unary())
                continue
            }
            return node
        }
    }

    private fun unary(): ExpressionNode {
        val token = peek()
        if (isOperator(token, "-") || isOperator(token, "+")) {
            val operator = take()!!.text
            val operand = unary()
            return if (operator == "-") ExpressionNode.Unary("-", operand) else operand
        }
        return power()
    }

    private fun power(): ExpressionNode {
        val base = atom()
        return if (isOperator(peek(), "^")) {
            take()
            ExpressionNode.Binary("^", base, unary())
        } else {
            base
        }
    }

    private fun atom(): ExpressionNode {
        val token = take() ?: throw IllegalArgumentException("unexpected end")
        if (token.type == TokenType.NUMBER) return ExpressionNode.Number(token.number)
        if (token.type == TokenType.NAME) {
            val name = token.text
            CONSTANTS[name]?.let { constant ->
                if (!isOperator(peek(), "(")) return ExpressionNode.Number(constant)
                take()
                expression()
                if (take()?.text != ")") throw IllegalArgumentException("expected )")
                return ExpressionNode.Number(constant)
            }
            val function = FUNCTIONS[name] ?: throw IllegalArgumentException("unknown name $name")
            if (!isOperator(peek(), "(")) {
                // функция без скобок: «√2» — это sqrt(2)
                return ExpressionNode.Function(name, power())
            }
            take()
            val argument = expression()
            if (take()?.text != ")") throw IllegalArgumentException("expected )")
            return ExpressionNode.Function(name, argument)
        }
        if (isOperator(token, "(")) {
            val inner = expression()
            if (take()?.text != ")") throw IllegalArgumentException("expected )")
            return inner
        }
        throw IllegalArgumentException("unexpected token")
    }
}

private val NUMBER_TOKEN = Regex("\\d*\\.?\\d*(e[-+]?\\d+)?")
private val NAME_TOKEN = Regex("[a-zA-Zа-яА-Я_]+")

private fun tokenizeExpression(source: String): List<ExpressionToken> {
    val text = source
        .replace("\u2212", "-")
        .replace("·", "*").replace("×", "*").replace("\u2219", "*")
        .replace(",", ".").replace("\u221a", "sqrt")
        .replace("\u03c0", "pi")
        .replace("\u00b2", "^2").replace("\u00b3", "^3")
        .replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    val tokens = mutableListOf<ExpressionToken>()
    var index = 0
    while (index < text.length) {
        val character = text[index]
        if (character.isWhitespace()) {
            index++
            continue
        }
        if (character.isDigit() || character == '.') {
            val piece = NUMBER_TOKEN.find(text, index)?.value ?: throw IllegalArgumentException("bad number")
            if (piece.isEmpty() || piece.none { it.isDigit() }) throw IllegalArgumentException("bad number")
            tokens.add(ExpressionToken(TokenType.NUMBER, piece, piece.toDouble()))
            index += piece.length
            continue
        }
        if (character.isLetter()) {
            val piece = NAME_TOKEN.find(text, index)?.value ?: throw IllegalArgumentException("bad name")
            tokens.add(ExpressionToken(TokenType.NAME, piece.lowercase(Locale.ROOT)))
            index += piece.length
            continue
        }
        if ("+-*/^%()".indexOf(character) >= 0) {
            tokens.add(ExpressionToken(TokenType.OPERATOR, character.toString()))
            index++
            continue
        }
        throw IllegalArgumentException("bad symbol $character")
    }
    return tokens
}

private fun evaluateExpression(node: ExpressionNode): Double = when (node) {
    is ExpressionNode.Number -> node.value
    is ExpressionNode.Unary -> -evaluateExpression(node.operand)
    is ExpressionNode.Function -> {
        val function = FUNCTIONS[node.name] ?: throw IllegalArgumentException("unknown function")
        function(evaluateExpression(node.argument))
    }
    is ExpressionNode.Binary -> {
        val left = evaluateExpression(node.left)
        val right = evaluateExpression(node.right)
        when (node.operator) {
            "+" -> left + right
            "-" -> left - right
            "*" -> left * right
            "/" -> left / right
            "%" -> left % right
            "^" -> left.pow(right)
            else -> throw IllegalArgumentException("unknown operator ${node.operator}")
        }
    }
}

/**
 * Kotlin port of the portable answer checker.
 *
 * The live interface grades answers with the JavaScript implementation
 * (``webapp/core.js`` -> ``CT.answer``); this Kotlin copy exists so that the
 * same algorithm is available to native code (reports, exports, future widgets)
 * and, most importantly, so the Android unit tests can assert that all three
 * implementations - Python (authoring), JavaScript (interface) and Kotlin
 * (native) - return identical verdicts for the shared vectors in
 * ``answer_vectors.json``.
 *
 * The algorithm has four tiers, documented in ``content_src/kit.py``:
 *
 * 1. canonical string match against the accepted spellings;
 * 2. choice tasks stop here (a lucky number is not an answer);
 * 3. exact numeric equality (``8/10`` == ``0,8`` == ``0.80``); a whole-number
 *    answer must stay exact, while fractions accept a hand-written rounding
 *    within ``5e-4 * max(1, |value|)`` (``5/6`` vs ``0,833``);
 * 4. expressions with roots or pi are compared numerically within
 *    ``1e-3 * max(1, |value|)``, but only when at least one of the two sides is
 *    written as an expression.
 */
object AnswerChecker {

    private val MINUS = Regex("[\u2212\u2013\u2014\u2015]")
    private val SPACE = Regex("[\\s\u00a0\u2009\u202f]")
    private val PREFIX_LONG = Regex("^(ответ|answer)\\s*[:=]?\\s*")
    private val PREFIX_SHORT = Regex("^[a-zа-я]{1,2}\\s*[:=]\\s*")
    private val WRAPPED = Regex("^\\((.*)\\)$")
    private val PLAIN_NUMBER =
        Regex("^[-+]?(\\d+(\\.\\d+)?|\\.\\d+)([-+*/]\\d+(\\.\\d+)?)*$")
    private val EXPRESSION_MARKERS = listOf("sqrt", "pi", "^", "(", ")")


    /** Canonical form of a student's answer: the same rules as in JS and Python. */
    fun normalize(value: String?): String {
        if (value.isNullOrEmpty()) return ""
        var s = value.trim().lowercase(Locale.ROOT)
        s = s.replace("\u00a0", " ")
        s = MINUS.replace(s, "-")
        s = s.replace("×", "*").replace("·", "*").replace("∙", "*")
        s = s.replace("х", "x").replace("у", "y")
        s = s.replace("π", "pi").replace("√", "sqrt")
        s = PREFIX_LONG.replace(s, "")
        s = PREFIX_SHORT.replace(s, "")
        s = SPACE.replace(s, "")
        s = WRAPPED.replace(s, "\$1")
        s = s.replace(",", ".")
        if (s.endsWith(".")) s = s.dropLast(1)
        return s
    }

    /** Value of a plain arithmetic answer («3», «0.75», «3/4», «-2,5») or null. */
    fun parseNumber(value: String?): Double? {
        val text = normalize(value)
        if (text.isEmpty() || !PLAIN_NUMBER.matches(text)) return null
        return arithmeticValue(text)
    }

    /** True when the answer is a whole number (compared exactly, never rounded). */
    fun isInteger(value: Double?): Boolean = value != null && abs(value % 1.0) < 1e-12

    /** True when the answer is written as an expression (root, pi, power). */
    fun isExpression(value: String?): Boolean {
        val text = normalize(value)
        if (text.isEmpty() || parseNumber(text) != null) return false
        return EXPRESSION_MARKERS.any { text.contains(it) }
    }

    /** Numeric value of a simple expression (mirrors ``CT.math.value``). */
    fun value(value: String?): Double? {
        val text = value ?: return null
        return try {
            val result = evaluateExpression(ExpressionParser(tokenizeExpression(text)).parse())
            if (result.isFinite()) result else null
        } catch (error: Exception) {
            null
        }
    }

    /** Decide whether [userAnswer] is correct for the task (see the class comment). */
    fun check(userAnswer: String?, task: JSONObject): Boolean {
        val user = normalize(userAnswer)
        if (user.isEmpty()) return false
        val variants = accepted(task)
        if (variants.contains(user)) return true
        if (task.optString("answerType", "short") == "choice") return false

        val userNumber = parseNumber(user)
        if (userNumber != null) {
            for (variant in variants) {
                val other = parseNumber(variant) ?: continue
                val difference = abs(userNumber - other)
                if (difference <= 1e-9) return true
                if (isInteger(other)) continue
                if (difference <= 5e-4 * maxOf(1.0, abs(other))) return true
            }
        }

        val userValue = value(user)
        if (userValue == null) return false
        val userIsExpression = isExpression(user)
        for (variant in variants) {
            if (!userIsExpression && !isExpression(variant)) continue
            val other = value(variant) ?: continue
            if (abs(userValue - other) <= 1e-3 * maxOf(1.0, abs(other))) return true
        }
        return false
    }

    /** Accepted spellings of the correct answer: ``accept`` plus the answer itself. */
    private fun accepted(task: JSONObject): List<String> {
        val result = mutableListOf<String>()
        fun add(raw: String?) {
            val normalized = normalize(raw)
            if (normalized.isNotEmpty() && !result.contains(normalized)) result.add(normalized)
        }
        val array: JSONArray? = task.optJSONArray("accept")
        if (array != null) {
            for (index in 0 until array.length()) add(array.optString(index))
        }
        when (val answer = task.opt("answer")) {
            is String -> add(answer)
            is JSONObject -> {
                add(answer.optString("ru"))
                add(answer.optString("en"))
            }
            is Number -> add(answer.toString())
        }
        return result
    }

    /* ------------------------------------------------------------- numbers --- */

    /**
     * Left-to-right arithmetic with the usual precedence, mirroring the JS helper
     * ``CT.answer.evalFraction``: sums of products and quotients of plain numbers.
     */
    private fun arithmeticValue(source: String): Double? {
        var index = 0
        val length = source.length

        fun readNumber(): Double? {
            val start = index
            while (index < length && (source[index].isDigit() || source[index] == '.')) index++
            if (index == start) return null
            return source.substring(start, index).toDoubleOrNull()
        }

        var termSign = 1.0
        if (index < length && (source[index] == '+' || source[index] == '-')) {
            if (source[index] == '-') termSign = -1.0
            index++
        }
        var total = 0.0
        while (true) {
            var product = readNumber() ?: return null
            while (index < length && (source[index] == '*' || source[index] == '/')) {
                val operator = source[index]
                index++
                val next = readNumber() ?: return null
                if (operator == '*') {
                    product *= next
                } else {
                    if (next == 0.0) return null
                    product /= next
                }
            }
            total += termSign * product
            if (index >= length) break
            termSign = when (source[index]) {
                '+' -> 1.0
                '-' -> -1.0
                else -> return null
            }
            index++
        }
        return total
    }

}
