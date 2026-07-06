package com.bfhs.parent.ui.navigation

import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.bfhs.parent.ui.components.BfhsBottomNavBar
import com.bfhs.parent.ui.components.BottomTab
import com.bfhs.parent.ui.screens.about.AboutSchoolScreen
import com.bfhs.parent.ui.screens.attendance.AttendanceScreen
import com.bfhs.parent.ui.screens.charges.ExtraChargesScreen
import com.bfhs.parent.ui.screens.dashboard.DashboardScreen
import com.bfhs.parent.ui.screens.fee.MonthlyFeeScreen
import com.bfhs.parent.ui.screens.language.LanguageScreen
import com.bfhs.parent.ui.screens.login.LoginScreen
import com.bfhs.parent.ui.screens.notifications.NotificationsScreen
import com.bfhs.parent.ui.screens.schoolprofile.SchoolProfileScreen
import com.bfhs.parent.ui.screens.settings.SettingsScreen
import com.bfhs.parent.ui.screens.splash.SplashScreen
import com.bfhs.parent.ui.screens.studentdetail.StudentDetailScreen
import com.bfhs.parent.ui.theme.BfhsColors

private val TAB_ROUTES = setOf(Routes.DASHBOARD, Routes.NOTIFICATIONS, Routes.SETTINGS)

@Composable
fun BfhsNavGraph(
    notificationType: String? = null,
    notificationStudentId: String? = null
) {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    // Consumed exactly once: without this, re-entering the Dashboard route
    // (e.g. pressing back from the deep-linked screen) would re-run the
    // LaunchedEffect below forever, since its keys (type, DASHBOARD) become
    // identical again — trapping the user in a back-navigation loop that
    // never reaches Home.
    var pendingNotificationType by remember { mutableStateOf(notificationType) }
    var pendingNotificationStudentId by remember { mutableStateOf(notificationStudentId) }

    // Background fills the whole screen (behind the system bars); the content is
    // then inset so no top bar hides under the clock/notch and the floating nav
    // clears the gesture bar — correct on every phone (notch, punch-hole, gesture
    // or button nav).
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(BfhsColors.BackgroundBase)
            .statusBarsPadding()
            .navigationBarsPadding()
    ) {
        NavHost(
            navController = navController,
            startDestination = Routes.SPLASH,
            enterTransition = { slideInHorizontally(tween(260)) { it / 4 } + fadeIn(tween(260)) },
            exitTransition = { fadeOut(tween(200)) },
            popEnterTransition = { fadeIn(tween(200)) },
            popExitTransition = { slideOutHorizontally(tween(260)) { it / 4 } + fadeOut(tween(260)) }
        ) {
            composable(Routes.SPLASH) {
                SplashScreen(
                    onNavigateToLogin = {
                        navController.navigate(Routes.LOGIN) {
                            popUpTo(Routes.SPLASH) { inclusive = true }
                        }
                    },
                    onNavigateToDashboard = {
                        navController.navigate(Routes.DASHBOARD) {
                            popUpTo(Routes.SPLASH) { inclusive = true }
                        }
                    }
                )
            }
            composable(Routes.LOGIN) {
                LoginScreen(
                    onLoginSuccess = {
                        navController.navigate(Routes.DASHBOARD) {
                            popUpTo(Routes.LOGIN) { inclusive = true }
                        }
                    }
                )
            }
            composable(Routes.DASHBOARD) {
                DashboardScreen(
                    onStudentClick = { navController.navigate(Routes.studentDetail(it)) },
                    onBellClick = { navController.navigateToTab(Routes.NOTIFICATIONS) }
                )
            }
            composable(Routes.NOTIFICATIONS) {
                NotificationsScreen()
            }
            composable(Routes.SETTINGS) {
                SettingsScreen(
                    onSchoolProfile = { navController.navigate(Routes.SCHOOL_PROFILE) },
                    onLanguage = { navController.navigate(Routes.LANGUAGE) },
                    onAbout = { navController.navigate(Routes.ABOUT) },
                    onLoggedOut = {
                        navController.navigate(Routes.LOGIN) {
                            popUpTo(0) { inclusive = true }
                        }
                    }
                )
            }
            composable(
                Routes.STUDENT_DETAIL,
                arguments = listOf(navArgument("studentId") { type = NavType.StringType })
            ) {
                StudentDetailScreen(onBack = { navController.popBackStack() })
            }
            composable(
                Routes.ATTENDANCE,
                arguments = listOf(navArgument("studentId") { type = NavType.StringType })
            ) {
                AttendanceScreen(onBack = { navController.popBackStack() })
            }
            composable(
                Routes.FEE,
                arguments = listOf(navArgument("studentId") { type = NavType.StringType })
            ) {
                MonthlyFeeScreen(onBack = { navController.popBackStack() })
            }
            composable(
                Routes.CHARGES,
                arguments = listOf(navArgument("studentId") { type = NavType.StringType })
            ) {
                ExtraChargesScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.SCHOOL_PROFILE) {
                SchoolProfileScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.LANGUAGE) {
                LanguageScreen(onBack = { navController.popBackStack() })
            }
            composable(Routes.ABOUT) {
                AboutSchoolScreen(onBack = { navController.popBackStack() })
            }
        }

        // Floating pill bottom nav — only on the three tab roots.
        if (currentRoute in TAB_ROUTES) {
            BfhsBottomNavBar(
                current = when (currentRoute) {
                    Routes.NOTIFICATIONS -> BottomTab.NOTICES
                    Routes.SETTINGS -> BottomTab.SETTINGS
                    else -> BottomTab.HOME
                },
                onTabSelected = { tab ->
                    val route = when (tab) {
                        BottomTab.HOME -> Routes.DASHBOARD
                        BottomTab.NOTICES -> Routes.NOTIFICATIONS
                        BottomTab.SETTINGS -> Routes.SETTINGS
                    }
                    navController.navigateToTab(route)
                },
                modifier = Modifier.align(Alignment.BottomCenter)
            )
        }

        // FCM deep link: once we land past splash, route to the right screen —
        // then immediately consume it, so backing out to Dashboard afterwards
        // behaves like a normal Home screen instead of re-triggering the jump.
        LaunchedEffect(pendingNotificationType, currentRoute) {
            val type = pendingNotificationType
            if (type != null && currentRoute == Routes.DASHBOARD) {
                pendingNotificationType = null
                pendingNotificationStudentId = null
                // Always open the Notifications tab (a tab-root with the bottom
                // nav) so the parent can read the message and still reach Home —
                // no dead-end student screen to get stuck on.
                navController.navigateToTab(Routes.NOTIFICATIONS)
            }
        }
    }
}

private fun NavHostController.navigateToTab(route: String) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
