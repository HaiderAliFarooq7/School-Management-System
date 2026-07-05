package com.bfhs.parent.di

import com.bfhs.parent.data.repository.AuthRepositoryImpl
import com.bfhs.parent.data.repository.NotificationRepositoryImpl
import com.bfhs.parent.data.repository.SchoolRepositoryImpl
import com.bfhs.parent.data.repository.StudentRepositoryImpl
import com.bfhs.parent.domain.repository.AuthRepository
import com.bfhs.parent.domain.repository.NotificationRepository
import com.bfhs.parent.domain.repository.SchoolRepository
import com.bfhs.parent.domain.repository.StudentRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(impl: AuthRepositoryImpl): AuthRepository

    @Binds
    @Singleton
    abstract fun bindStudentRepository(impl: StudentRepositoryImpl): StudentRepository

    @Binds
    @Singleton
    abstract fun bindNotificationRepository(impl: NotificationRepositoryImpl): NotificationRepository

    @Binds
    @Singleton
    abstract fun bindSchoolRepository(impl: SchoolRepositoryImpl): SchoolRepository
}
