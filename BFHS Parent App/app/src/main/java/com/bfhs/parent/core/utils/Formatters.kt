package com.bfhs.parent.core.utils

import java.text.NumberFormat
import java.util.Locale

object Formatters {

    /** PKR currency in the design's format: "Rs. 12,500". */
    fun rupees(amount: Long): String {
        val grouped = NumberFormat.getIntegerInstance(Locale.US).format(amount)
        return "Rs. $grouped"
    }
}
