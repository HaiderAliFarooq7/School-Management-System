package com.bfhs.parent.data.network

import com.bfhs.parent.data.datastore.SessionManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/** Attaches the stored JWT as a Bearer token to every request except login. */
@Singleton
class AuthInterceptor @Inject constructor(
    private val sessionManager: SessionManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        if (request.url.encodedPath.endsWith("/login")) {
            return chain.proceed(request)
        }
        val token = runBlocking { sessionManager.tokenOnce() }
        val authed = if (token.isNullOrBlank()) request else {
            request.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        }
        return chain.proceed(authed)
    }
}
