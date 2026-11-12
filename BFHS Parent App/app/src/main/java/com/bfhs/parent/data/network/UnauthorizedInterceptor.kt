package com.bfhs.parent.data.network

import com.bfhs.parent.data.datastore.SessionManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Drops the stored session as soon as the server rejects the JWT.
 *
 * The backend issues 8-hour tokens (JWT_EXPIRE_MINUTES), so a parent who opens
 * the app the next morning is carrying an expired one. Splash only checks that
 * a token *exists*, not that it still works, so before this the app would go
 * straight to the dashboard and then fail every single request with "Session
 * expired" — with no way out except finding Logout buried in Settings.
 *
 * Clearing the session here flips [SessionManager.token] to null, which the nav
 * graph observes and turns into an automatic trip back to the Login screen.
 *
 * A 401 on the login call itself means "wrong mobile/password" — that is the
 * login screen's business, so it is deliberately left alone.
 */
@Singleton
class UnauthorizedInterceptor @Inject constructor(
    private val sessionManager: SessionManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val response = chain.proceed(request)

        if (response.code == HTTP_UNAUTHORIZED && !request.url.encodedPath.endsWith("/login")) {
            runBlocking { sessionManager.clearSession() }
        }
        return response
    }

    private companion object {
        const val HTTP_UNAUTHORIZED = 401
    }
}
