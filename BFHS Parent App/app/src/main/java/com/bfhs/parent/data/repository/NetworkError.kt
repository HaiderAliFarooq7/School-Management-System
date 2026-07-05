package com.bfhs.parent.data.repository

import android.util.Log
import com.bfhs.parent.BuildConfig
import retrofit2.HttpException
import java.io.IOException
import java.io.InterruptedIOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import javax.net.ssl.SSLException

private const val TAG = "BfhsNetwork"

/**
 * Maps a network/HTTP failure to a real, human-readable message — never a
 * generic "No Internet" for what is actually a wrong URL, a cold-starting
 * server, an auth error, or a 5xx.
 *
 * The full technical cause is always logged (Logcat tag [TAG]); in debug builds
 * it is also appended to the on-screen message so the real error is visible
 * while testing, per the connection-diagnostics requirements.
 */
internal fun Throwable.userMessage(): String {
    Log.w(TAG, "Request failed: ${this::class.simpleName}: ${message}", this)

    val base = when (this) {
        is UnknownHostException ->
            "Can't reach the server. Check the server address and your internet connection."
        is SocketTimeoutException, is InterruptedIOException ->
            "The server took too long to respond. It may be waking up — please try again."
        is ConnectException ->
            "Could not connect to the server. Please try again in a moment."
        is SSLException ->
            "Secure (SSL) connection to the server failed."
        is HttpException -> when (code()) {
            400 -> "Invalid request (400)."
            401 -> "Session expired or unauthorized (401). Please sign in again."
            403 -> "You don't have permission to view this (403)."
            404 -> "Not found on the server (404)."
            408 -> "The request timed out (408). Please try again."
            in 500..599 -> "The server had a problem (${code()}). Please try again shortly."
            else -> "Server returned an error (${code()})."
        }
        is IOException ->
            "Network error. Please check your connection and try again."
        else ->
            "Something went wrong. Please try again."
    }

    return if (BuildConfig.DEBUG) {
        "$base\n[${this::class.simpleName}: ${message ?: "no detail"}]"
    } else {
        base
    }
}
