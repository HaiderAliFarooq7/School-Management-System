package com.bfhs.parent.core

/** Wrapper for data that may come from network or cache, with loading/error states. */
sealed class Resource<out T> {
    data object Loading : Resource<Nothing>()
    data class Success<T>(val data: T, val fromCache: Boolean = false) : Resource<T>()
    data class Error<T>(val message: String, val cached: T? = null) : Resource<T>()
}
