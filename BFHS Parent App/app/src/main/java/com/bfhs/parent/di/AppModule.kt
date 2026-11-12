package com.bfhs.parent.di

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.preferencesDataStore
import androidx.room.Room
import com.bfhs.parent.BuildConfig
import com.bfhs.parent.data.local.AttendanceDao
import com.bfhs.parent.data.local.BfhsDatabase
import com.bfhs.parent.data.local.ExtraChargeDao
import com.bfhs.parent.data.local.FeeDao
import com.bfhs.parent.data.local.NotificationDao
import com.bfhs.parent.data.local.SchoolDao
import com.bfhs.parent.data.local.StudentDao
import com.bfhs.parent.data.network.AuthInterceptor
import com.bfhs.parent.data.network.BfhsApiService
import com.bfhs.parent.data.network.UnauthorizedInterceptor
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

private val Context.appDataStore: DataStore<Preferences> by preferencesDataStore(name = "bfhs_parent_prefs")

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDataStore(@ApplicationContext context: Context): DataStore<Preferences> =
        context.appDataStore

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        unauthorizedInterceptor: UnauthorizedInterceptor,
    ): OkHttpClient {
        // Full request/response logging (URL, method, headers, body, status) in
        // debug builds; nothing in release. Visible in Logcat under the "OkHttp"
        // tag. The Authorization header is redacted so JWTs aren't logged raw.
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
            else HttpLoggingInterceptor.Level.NONE
            redactHeader("Authorization")
        }
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            // Must sit after authInterceptor so it sees the response to an
            // already-authenticated request and can drop an expired session.
            .addInterceptor(unauthorizedInterceptor)
            .addInterceptor(logging)
            // The backend runs on Render's free tier, which spins down when idle
            // and can take ~50s to cold-start. Generous timeouts stop that first
            // request being reported as a (false) network failure.
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .callTimeout(70, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): BfhsApiService =
        retrofit.create(BfhsApiService::class.java)

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): BfhsDatabase =
        Room.databaseBuilder(context, BfhsDatabase::class.java, "bfhs_parent.db")
            .fallbackToDestructiveMigration()
            .build()

    @Provides fun provideStudentDao(db: BfhsDatabase): StudentDao = db.studentDao()
    @Provides fun provideAttendanceDao(db: BfhsDatabase): AttendanceDao = db.attendanceDao()
    @Provides fun provideFeeDao(db: BfhsDatabase): FeeDao = db.feeDao()
    @Provides fun provideExtraChargeDao(db: BfhsDatabase): ExtraChargeDao = db.extraChargeDao()
    @Provides fun provideNotificationDao(db: BfhsDatabase): NotificationDao = db.notificationDao()
    @Provides fun provideSchoolDao(db: BfhsDatabase): SchoolDao = db.schoolDao()
}
